#!/usr/bin/env python3
"""One explicitly approved web-only synthetic assistant production release."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import time
import urllib.request
import urllib.error

BASE=Path('/opt/abap-public-rag-production/releases/0ef5085524b6-r2/compose.deploy.yaml')
ENVFILE=Path('/etc/abap/production.env')
ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-assistant-production-release-20261104-1.json'
RELEASE=Path('/opt/abap-advanced-assistant/releases/20261104-1')
CREDENTIALS=Path('/etc/abap/credentials/advanced-assistant')
OLD='sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9'
OLD_TAG='abap:public-rag-0ef5085524b6-r3'
DB='sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280'
MODELS=['openrouter:nvidia/nemotron-3.5-lightning:free','openrouter:cohere/north-mini-code:free']
ENV={'PATH':'/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/nonexistent','LC_ALL':'C','DOCKER_HOST':'unix:///var/run/docker.sock'}
class Stop(Exception):pass
def need(value,code):
    if not value:raise Stop(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path,limit):
    with path.open('rb') as f:b=f.read(limit+1)
    need(len(b)<=limit,'input_size_limit');return b
def digest_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def call(*args,timeout=60,data=None):
    try:p=subprocess.run(list(args),input=data,capture_output=True,env=ENV,timeout=timeout)
    except subprocess.TimeoutExpired:raise Stop('command_timeout') from None
    need(p.returncode==0,'command_failed_raw_output_suppressed');return p.stdout
def docker(*args,**kwargs):return call('/usr/bin/docker','--host','unix:///var/run/docker.sock',*args,**kwargs)
def inventory():
    ids=docker('ps','-aq').decode().split();need(0<len(ids)<100,'container_inventory_limit')
    return json.loads(docker('inspect',*ids))
def service(rows,name):
    found=[r for r in rows if (r['Config'].get('Labels') or {}).get('com.docker.compose.project')=='abap-deploy' and
        (r['Config'].get('Labels') or {}).get('com.docker.compose.service')==name and r['State']['Running']]
    need(len(found)==1,'production_service_identity_ambiguous');return found[0]
def stable(rows,exclude):
    return sorted((r['Id'],r['Image'],r['State']['Running'],r['RestartCount'],sha(json.dumps(r['Config'],sort_keys=True).encode())) for r in rows if r['Id']!=exclude)
def ledger(db):
    sql='SELECT migration_name FROM schema_migrations ORDER BY migration_name'
    command='exec psql -XAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"'
    return docker('exec',db,'/bin/sh','-c',command,'approved-release-ledger',sql).decode().splitlines()
def compose(files,*args,**kwargs):
    cmd=['compose','--project-directory',str(BASE.parent),'--env-file',str(ENVFILE),'-p','abap-deploy','-f',str(BASE)]
    for f in files:cmd+=['-f',str(Path(f) if Path(f).is_absolute() else RELEASE/f)]
    return docker(*cmd,*args,**kwargs)
def envmap(rows):return dict(row.split('=',1) for row in rows)
def config_preserved(before,after):
    a=before['services'];b=after['services'];need(all(v==b.get(k) for k,v in a.items() if k!='web'),'other_service_configuration_changed')
    old=a['web'];new=b['web']
    clean=lambda e:{k:v for k,v in e.items() if not k.startswith('ABAP_ASSISTANT_') and k not in ['ABAP_ADVANCED_ASSISTANT_ENABLED','ABAP_ENVIRONMENT']}
    need(clean(old.get('environment',{}))==clean(new.get('environment',{})),'nonassistant_environment_changed')
    need(all(v in new.get('volumes',[]) for v in old.get('volumes',[])),'existing_web_volume_changed')
    need(all(old.get(k)==new.get(k) for k in ['networks','secrets','ports','command','depends_on']),'existing_web_runtime_changed')
def write_new(path,data,mode=0o640,gid=0):
    need(path.resolve()==path and not path.is_symlink(),'unsafe_install_path')
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode),'wb') as f:
        os.fchown(f.fileno(),0,gid);os.fchmod(f.fileno(),mode);f.write(data);f.flush();os.fsync(f.fileno())
def checkpoint(result):
    data=json.dumps(result,indent=2).encode();need(len(data)<262144,'receipt_size_limit')
    temporary=RECEIPT.with_name(RECEIPT.name+'.next')
    with os.fdopen(os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600),'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(temporary,RECEIPT)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def http(path):
    opener=urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(urllib.request.Request('http://127.0.0.1:8000'+path,headers={'Host':'app.dennisbasadre.com'}),timeout=5) as r:return r.status,r.read(200000)
    except urllib.error.HTTPError as e:return e.code,b''
def wait_health():
    end=time.monotonic()+120
    while True:
        try:
            a,body=http('/health');b,ready=http('/ready')
            if a==b==200 and json.loads(body).get('status')=='healthy' and json.loads(ready).get('status')=='ready':return {'health':a,'ready':b}
        except Exception:pass
        need(time.monotonic()<end,'application_health_timeout');time.sleep(2)
def baseline_smoke(rag):
    result=wait_health();code,page=http('/login');need(code==200,'login_smoke_failed')
    need((b'public-rag-chat.js' in page)==rag,'public_rag_ui_marker_changed');result['login']=code;result['rag_ui_preserved']=True;return result
def validate_proof(key,proof,now):
    need(sorted(r.get('id','') for r in proof)==sorted(MODELS),'unexpected_model_proof')
    for r in proof:
        need(r.get('key_fingerprint')==sha(key) and 0<=now-r.get('checked_at',0)<=86400 and
            all(r.get(k) is True for k in ['free_eligible','access_verified','business_protocol_verified','english_verified','japanese_verified']),'invalid_or_expired_model_proof')
def rollback_web(rag):
    compose(['rollback-web.json'],'up','-d','--no-deps','--no-build','--pull','never','web',timeout=120)
    restored=service(inventory(),'web');need(restored['Image']==OLD,'rollback_image_mismatch')
    return {'status':'PASS','smoke':baseline_smoke(rag),'assistant_active':False}
def main():
    global RECEIPT,RELEASE
    need(os.geteuid()==0 and len(sys.argv)==1,'authenticated_sudo_required');os.umask(0o077)
    source=Path(__file__).resolve().parent
    manifest_raw=read(source/'release-inputs.json',131072)
    need(sha(manifest_raw)==globals().get('__manifest_sha256__'),'release_manifest_digest_mismatch')
    manifest=json.loads(manifest_raw)
    revision=manifest.get('revision','20261104-1');need(revision in ['20261104-1','20261104-r2'],'unapproved_release_revision')
    RECEIPT=ROOT/('approved-assistant-production-release-'+revision+'.json')
    RELEASE=Path('/opt/abap-advanced-assistant/releases')/revision
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'unsafe_receipt_parent')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'release_already_consumed_do_not_repeat')
    need(not RELEASE.exists() and not RELEASE.is_symlink(),'release_directory_already_exists')
    need(BASE.resolve()==BASE and sha(BASE.read_bytes())==manifest['base_compose_sha256'],'base_compose_drift')
    need(ENVFILE.resolve()==ENVFILE and ENVFILE.stat().st_uid==0 and stat.S_IMODE(ENVFILE.stat().st_mode)==0o600,'production_environment_permissions_changed')
    original_env_digest=sha(ENVFILE.read_bytes())
    for name,h in manifest['files'].items():
        need(Path(name).name==name,'unsafe_bundle_filename');need(digest_file(source/name)==h,'bundle_digest_mismatch')
    key=read(source/'openrouter-key',4096).decode('utf-8-sig').strip().encode();need(key and b'\n' not in key and b'\r' not in key,'invalid_credential')
    proof_raw=read(source/'cloud-validation.json',131072);proof=json.loads(proof_raw);validate_proof(key,proof,time.time())
    need(shutil.disk_usage(ROOT).free>=4000000000,'insufficient_disk_reserve')
    rows=inventory();web=service(rows,'web');db=service(rows,'database')
    need(web['Image']==manifest.get('expected_current_image',OLD) and db['Image']==DB,'production_release_drift')
    need(json.loads(docker('image','inspect',OLD_TAG))[0]['Id']==OLD,'rollback_image_tag_drift')
    unaffected=stable(rows,web['Id']);before_ledger=ledger(db['Id'])
    expected_count=manifest.get('expected_ledger_count',13);need(expected_count in [13,16],'unapproved_migration_baseline')
    need(before_ledger==manifest['migration_names'][:expected_count],'migration_ledger_drift')
    rag=b'public-rag-chat.js' in http('/login')[1];previous=baseline_smoke(rag)
    before=json.loads(compose(manifest.get('baseline_overlays',[]),'config','--format','json'))
    defaults=json.loads(docker('image','inspect',web['Image']))[0]['Config'].get('Env',[])
    need(envmap(web['Config']['Env'])=={**envmap(defaults),**{k:str(v) for k,v in before['services']['web']['environment'].items()}},'runtime_environment_drift')
    result={'operation':'approved-assistant-production-release-'+revision,'status':'RUNNING','stage':'install_release_assets','started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'accepted_unrehearsed_disaster_recovery_risk':True,'baseline':previous,'b2_requests':0,'web_changed':False,'migrations_applied':False}
    write_new(RECEIPT,json.dumps(result).encode(),0o600)
    try:
        RELEASE.mkdir(parents=True,mode=0o750)
        for name in ['disabled-web.json','activation-web.json','migration-once.json','rollback-web.json']:
            write_new(RELEASE/name,read(source/name,131072))
        need(CREDENTIALS.resolve()==CREDENTIALS and not CREDENTIALS.is_symlink(),'credential_directory_symlink')
        if not CREDENTIALS.exists():
            CREDENTIALS.mkdir(mode=0o750);os.chown(CREDENTIALS,0,10001);os.chmod(CREDENTIALS,0o750)
        need(CREDENTIALS.stat().st_uid==0 and CREDENTIALS.stat().st_gid==10001 and stat.S_IMODE(CREDENTIALS.stat().st_mode)==0o750,'credential_directory_permissions')
        for name,data in [('openrouter-key',key),('cloud-validation.json',proof_raw)]:
            path=CREDENTIALS/name
            if path.exists():
                s=path.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_gid==10001 and stat.S_IMODE(s.st_mode)==0o640 and path.read_bytes()==data,'existing_credential_conflict')
            else:write_new(path,data,0o640,10001)
        result['credentials_installed']=True;result['stage']='load_approved_image';checkpoint(result)
        # Only the unique candidate tag is in this authenticated archive.
        docker('image','load','--input',str(source/'candidate-image.tar'),timeout=180)
        candidate=json.loads(docker('image','inspect',manifest['image']['tag']))[0]
        need(candidate['Id'] in [manifest['image']['image_id'],manifest['image']['config_digest']] and candidate['RootFS']['Layers']==manifest['image']['layers'],'loaded_candidate_identity_mismatch')
        result['candidate_image_id']=candidate['Id']
        disabled=json.loads(compose(['disabled-web.json'],'config','--format','json'));config_preserved(before,disabled)
        env=disabled['services']['web']['environment'];need(env['ABAP_ADVANCED_ASSISTANT_ENABLED']=='false' and env['ABAP_ASSISTANT_REMOTE_APPROVED']=='false' and env['ABAP_ASSISTANT_DEMO_ONLY']=='true' and env['ABAP_ASSISTANT_N8N_WORKFLOWS']=='','disabled_assistant_boundary_failed')
        if expected_count==13:
            result['stage']='apply_migrations_014_016';checkpoint(result)
            compose(['disabled-web.json','migration-once.json'],'run','--rm','--no-deps','--pull','never','-e','PGOPTIONS=-c lock_timeout=5000 -c statement_timeout=60000','migrate',timeout=120)
            need(ledger(db['Id'])==manifest['migration_names'],'post_migration_ledger_mismatch');result['migrations_applied']=True
        else:result['existing_migrations_reused']=True
        result['stage']='deploy_disabled_web';result['web_changed']=True;checkpoint(result)
        compose(['disabled-web.json'],'up','-d','--no-deps','--no-build','--pull','never','web',timeout=120)
        newweb=service(inventory(),'web');need(newweb['Image']==candidate['Id'],'disabled_web_wrong_image')
        result['disabled_smoke']=baseline_smoke(rag);need(http('/ai-assistant/advanced')[0]==404,'disabled_assistant_route_exposed')
        result['stage']='validate_installed_provider_configuration';checkpoint(result)
        program="import json;from assistant_gateway import configured_models; print(json.dumps([m.public() for m in configured_models()]))"
        # Remote-approved is false here; verify key/proof readability and registry
        # with an explicit process-only validation flag, without making API calls.
        models=json.loads(docker('exec','-e','ABAP_ASSISTANT_REMOTE_APPROVED=true',newweb['Id'],'python','-B','-c',program))
        need(sorted(m['id'] for m in models)==sorted(MODELS) and all(m['available'] for m in models),'installed_model_registry_unavailable')
        result['installed_models']=[{'id':m['id'],'available':m['available']} for m in models]
        result['stage']='activate_synthetic_only_web';checkpoint(result)
        compose(['disabled-web.json','activation-web.json'],'up','-d','--no-deps','--no-build','--pull','never','web',timeout=120)
        current=service(inventory(),'web');need(current['Image']==candidate['Id'],'active_web_wrong_image')
        actual=envmap(current['Config']['Env']);need(actual['ABAP_ADVANCED_ASSISTANT_ENABLED']=='true' and actual['ABAP_ASSISTANT_REMOTE_APPROVED']=='true' and actual['ABAP_ASSISTANT_DEMO_ONLY']=='true' and actual['ABAP_ASSISTANT_N8N_WORKFLOWS']=='','active_assistant_boundary_failed')
        result['active_smoke']=baseline_smoke(rag);need(http('/ai-assistant/advanced')[0]==303,'anonymous_assistant_boundary_failed')
        need(stable([r for r in inventory() if r['Id']!=current['Id']],None)==unaffected,'unrelated_container_state_changed')
        need(sha(ENVFILE.read_bytes())==original_env_digest,'original_environment_changed')
        result.update(status='PASS-deployed-synthetic-assistant-awaiting-authenticated-browser-smoke',stage='awaiting_browser_smoke',assistant_active=True,public_url='https://app.dennisbasadre.com/ai-assistant/advanced',web_container_id=current['Id'],other_containers_preserved=True,original_environment_preserved=True)
    except BaseException as error:
        result.update(status='FAIL-release-stopped',failure={'stage':result['stage'],'code':str(error) if isinstance(error,Stop) else 'internal_error_raw_output_suppressed'})
        if result['web_changed']:
            try:
                result['rollback']=rollback_web(rag);result['assistant_active']=False
            except BaseException:result['rollback']={'status':'BLOCKED-manual-intervention-required'}
        else:result['rollback']={'status':'NOT-NEEDED-original-web-unchanged'}
    finally:
        try:
            current=service(inventory(),'web');result['other_containers_preserved']=stable([r for r in inventory() if r['Id']!=current['Id']],None)==unaffected
            result['final_migration_count']=len(ledger(db['Id']))
        except BaseException:result['final_readonly_checks']='BLOCKED'
        if result['status'].startswith('PASS-deployed') and (result.get('other_containers_preserved') is not True or result.get('final_migration_count')!=len(manifest['migration_names']) or result.get('final_readonly_checks')=='BLOCKED'):
            result['status']='FAIL-final-production-invariant'
            try:result['rollback']=rollback_web(rag);result['assistant_active']=False
            except BaseException:result['rollback']={'status':'BLOCKED-manual-intervention-required'}
        result['completed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();checkpoint(result)
        # Remove only the exact private transfer copy after root-owned installation.
        staged_key=source/'openrouter-key'
        try:
            if result.get('credentials_installed') and staged_key.is_file() and digest_file(staged_key)==manifest['files']['openrouter-key']:
                staged_key.unlink();result['temporary_credential_copy_removed']=True;checkpoint(result)
        except BaseException:result['temporary_credential_cleanup']='BLOCKED-private-transfer-file-retained';checkpoint(result)
    return result
if __name__=='__main__':
    def interrupted(signum,frame):raise Stop('operator_interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-review-protected-release-receipt' if RECEIPT.exists() else 'BLOCKED-before-deployment','code':str(error) if isinstance(error,Stop) else 'precondition_unavailable'}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('status','').startswith('PASS-deployed') else 1)
