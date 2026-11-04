#!/usr/bin/env python3
"""Renew only the two approved free models; host job uses the existing web image."""
import fcntl
import hashlib
import json
import os
import signal
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time

APPROVED=('openrouter:nvidia/nemotron-3.5-lightning:free','openrouter:cohere/north-mini-code:free')
TTL=86400
RENEW_BEFORE=21600
HOST_DIRECTORY=Path('/etc/abap/credentials/advanced-assistant')
PROOF=HOST_DIRECTORY/'cloud-validation.json'
CONTAINER_DIRECTORY='/run/assistant-validation'
CONTAINER_PROOF=CONTAINER_DIRECTORY+'/cloud-validation.json'
LOCK=Path('/run/abap-assistant-validation/renew.lock')
FIELDS={'id','provider','model','free_eligible','native_tools_advertised','checked_at',
        'key_fingerprint','access_verified','business_protocol_verified','english_verified',
        'japanese_verified','native_tools_verified'}
class RenewalError(Exception):pass
def require(value,code):
    if not value:raise RenewalError(code)
def digest(data):return hashlib.sha256(data).hexdigest()
def read_json(path):
    with path.open('rb') as f:raw=f.read(131073)
    require(len(raw)<=131072,'proof_too_large');return raw,json.loads(raw)
def combined_probe(model):
    from assistant_gateway import Gateway,Model
    expected={'english':'CLOUD_OK','japanese':'確認しました。','business_request':{'tool':'leads'}}
    answer,_=Gateway([Model(model.id,model.provider,model.model,model.key,model.endpoint,True)]).generate(
        model.id,'Return ONLY the exact JSON object '+json.dumps(expected,ensure_ascii=False)+
        '. Synthetic capability verification only. Do not execute any tool or action.',
        'Verify English, Japanese, and the read-only business JSON protocol.')
    # No provider text, headers or errors enter logs or the evidence file.
    cleaned=re.sub(r'^```(?:json)?\s*|\s*```$','',answer.strip())
    require(json.loads(cleaned)==expected,'synthetic_probe_not_verified')
def renew(environment,previous,now,fetch=None,probe=None):
    """Pure admission/renewal logic, with injectable provider calls for fixtures."""
    from assistant_gateway import configured_models
    from assistant_cloud_validate import get_catalog,free_openrouter
    require(environment.get('ABAP_ADVANCED_ASSISTANT_ENABLED')=='true' and
        environment.get('ABAP_ASSISTANT_REMOTE_APPROVED')=='true' and
        environment.get('ABAP_ASSISTANT_DEMO_ONLY')=='true' and
        not environment.get('ABAP_ASSISTANT_N8N_WORKFLOWS','') and
        not environment.get('ABAP_ASSISTANT_GEMINI_MODELS','') and
        not environment.get('ABAP_ASSISTANT_COMPATIBLE_MODELS','') and
        environment.get('ABAP_ASSISTANT_ALLOW_LOCAL_DEVELOPMENT','false')!='true',
        'approved_synthetic_configuration_required')
    # Explicit operator job can recheck expired evidence; web admission is unchanged.
    env=dict(environment);env.pop('ABAP_ASSISTANT_CLOUD_VALIDATION_FILE',None)
    models=configured_models(env)
    require(sorted(m.id for m in models)==sorted(APPROVED),'unexpected_configured_models')
    require(isinstance(previous,list) and len(previous)==2 and
        sorted(r.get('id','') for r in previous)==sorted(APPROVED),'reviewed_seed_evidence_required')
    records={r['id']:{k:v for k,v in r.items() if k in FIELDS} for r in previous}
    for m in models:
        row=records[m.id]
        require(m.key and row.get('key_fingerprint')==digest(m.key.encode()) and
            type(row.get('checked_at')) in (int,float) and row['checked_at']<=now and
            all(row.get(k) is True for k in ['business_protocol_verified','english_verified','japanese_verified']),
            'credential_or_seed_changed_manual_validation_required')
    due={m.id for m in models if now-records[m.id]['checked_at']>=TTL-RENEW_BEFORE or
         records[m.id].get('access_verified') is not True or records[m.id].get('free_eligible') is not True}
    result={'status':'SKIP-not-due','changed':False,'requests':0,'models':[]}
    if not due:return result
    fetch=fetch or get_catalog;probe=probe or combined_probe
    try:
        result['requests']+=1
        account=fetch('openrouter.ai','/api/v1/key',{'Authorization':'Bearer '+models[0].key})['data']
        if type(account.get('limit')) not in (int,float) or account['limit']!=0:
            for row in records.values():row['access_verified']=False
            return {**result,'status':'REVIEW_REQUIRED-zero_limit','changed':True,'records':list(records.values()),
                'models':[{'id':m.id,'status':'zero_credit_limit_not_confirmed'} for m in models]}
        result['requests']+=1
        free={r['id']:r for r in free_openrouter(fetch('openrouter.ai','/api/v1/models'))}
    except Exception:return {**result,'status':'TEMPORARY_FAILURE-metadata'}
    for model in models:
        row=records[model.id]
        if model.id not in free:
            row.update(free_eligible=False,access_verified=False);result['changed']=True
            result['models'].append({'id':model.id,'status':'not_currently_free'});continue
        if model.id not in due:continue
        try:
            result['requests']+=1;probe(model)
            row.update(free[model.id],id=model.id,provider='openrouter',model=model.model,
                checked_at=now,key_fingerprint=digest(model.key.encode()),access_verified=True,
                business_protocol_verified=True,english_verified=True,japanese_verified=True,native_tools_verified=False)
            result['changed']=True;result['models'].append({'id':model.id,'status':'renewed'})
        except Exception:result['models'].append({'id':model.id,'status':'temporary_probe_failure'})
    result['status']='PASS' if all(r['status']=='renewed' for r in result['models']) else 'PARTIAL_OR_REVIEW_REQUIRED'
    if result['changed']:result['records']=list(records.values())
    return result
def probe_main():
    require(os.environ.get('ABAP_ASSISTANT_CLOUD_VALIDATION_FILE')==CONTAINER_PROOF,'directory_mount_required')
    _,previous=read_json(Path(CONTAINER_PROOF))
    return renew(dict(os.environ),previous,time.time())
def atomic_publish(path,original,records):
    require(path.resolve()==path and path.parent.resolve()==path.parent,'proof_symlink_rejected')
    s=path.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_gid==10001 and
        stat.S_IMODE(s.st_mode)==0o640,'proof_permissions_changed')
    require(sorted(r.get('id','') for r in records)==sorted(APPROVED),'unexpected_published_models')
    data=(json.dumps(records,indent=2,ensure_ascii=False)+'\n').encode();require(len(data)<=131072,'proof_too_large')
    fd,name=tempfile.mkstemp(prefix='.cloud-validation-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            os.fchown(f.fileno(),0,10001);os.fchmod(f.fileno(),0o640);f.write(data);f.flush();os.fsync(f.fileno())
        require(read_json(path)[0]==original,'proof_changed_during_renewal')
        os.replace(name,path)
        directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(name):os.unlink(name) # Only this invocation's temporary file.
def docker(*args,stdin=None):
    p=subprocess.run(['/usr/bin/docker','--host','unix:///var/run/docker.sock',*args],input=stdin,
        capture_output=True,timeout=180,env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent'})
    require(p.returncode==0 and len(p.stdout)<=131072,'renewal_process_failed');return p.stdout
def host_main():
    require(os.geteuid()==0,'host_root_service_required')
    require(LOCK.parent.resolve()==LOCK.parent and LOCK.parent.stat().st_uid==0 and
        stat.S_IMODE(LOCK.parent.stat().st_mode)==0o700,'private_runtime_directory_required')
    with os.fdopen(os.open(LOCK,os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600),'wb') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'SKIP-already-running','changed':False,'requests':0}
        require(HOST_DIRECTORY.resolve()==HOST_DIRECTORY and HOST_DIRECTORY.stat().st_uid==0 and
            HOST_DIRECTORY.stat().st_gid==10001 and stat.S_IMODE(HOST_DIRECTORY.stat().st_mode)==0o750,'proof_directory_permissions_changed')
        original,_=read_json(PROOF)
        ids=docker('ps','-q','--filter','label=com.docker.compose.project=abap-deploy',
            '--filter','label=com.docker.compose.service=web','--filter','status=running').decode().splitlines()
        require(len(ids)==1,'production_web_identity_ambiguous')
        info=json.loads(docker('inspect',ids[0]))[0]
        require(any(m.get('Type')=='bind' and m.get('Source')==str(HOST_DIRECTORY) and
            m.get('Destination')==CONTAINER_DIRECTORY and m.get('RW') is False for m in info.get('Mounts',[])),
            'readonly_directory_mount_required')
        result=json.loads(docker('exec','-i',ids[0],'python','-B','-','--probe',stdin=Path(__file__).read_bytes()))
        if result.get('changed'):atomic_publish(PROOF,original,result['records'])
        return {k:v for k,v in result.items() if k!='records'}
if __name__=='__main__':
    probing=sys.argv[1:]==['--probe']
    if probing:
        def expired(signum,frame):raise SystemExit(2)
        signal.signal(signal.SIGALRM,expired);signal.alarm(150)
    try:
        result=probe_main() if probing else host_main() if len(sys.argv)==1 else {'status':'BLOCKED-invalid_arguments'}
    except Exception:result={'status':'BLOCKED-renewal-prerequisite','changed':False}
    print(json.dumps(result,ensure_ascii=False))
    # Structured partial/invalidation results must reach the host publisher.
    # Only the host service maps those outcomes to a failing systemd status.
    raise SystemExit(0 if probing or result.get('status','').startswith(('PASS','SKIP')) else 1)
