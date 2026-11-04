#!/usr/bin/env python3
"""Approved image-only web maintenance; all operational settings stay identical."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import stat
import sys
import types

OLD='sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49'
NEW='sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c'
TAG='abap:security-20261104-1'
ARCHIVE_SHA='7d55f80f021d0e55461c33cb5beab2d157c920cdd7be374ef315a55858bc94aa'
ARCHIVE_SIZE=114463232
HELPER_SHA='042411390709fcb874833d3691c884b49dc7794ae87cce8a31d9e784458b63d0'
ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-web-security-image-20261104-1.json'
RELEASE=Path('/opt/abap-advanced-assistant/releases/20261104-r2')
OVERLAY=RELEASE/'security-web-20261104.json'
OLD_FILES=['disabled-web.json','activation-web.json','validation-renewal.json']
MODELS=['openrouter:nvidia/nemotron-3.5-lightning:free','openrouter:cohere/north-mini-code:free']
OVERLAY_BYTES=(json.dumps({'services':{'web':{'image':TAG}}},indent=2)+'\n').encode()
class Stop(Exception):pass
def need(value,code):
    if not value:raise Stop(code)
def sha(data):return hashlib.sha256(data).hexdigest()

def image_only(before,after):
    expected=json.loads(json.dumps(before))
    expected['services']['web']['image']=TAG
    need(after==expected,'change_beyond_web_image_rejected')

def checkpoint(report,first=False):
    flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_EXCL if first else os.O_TRUNC)
    with os.fdopen(os.open(RECEIPT,flags,0o600),'w') as f:
        os.fchmod(f.fileno(),0o600);json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())

def models(p,cid):
    code="from assistant_gateway import configured_models; import json; print(json.dumps([{'id':m.id,'available':m.available} for m in configured_models()]))"
    result=json.loads(p.docker('exec',cid,'python','-B','-c',code))
    need(sorted(x['id'] for x in result)==sorted(MODELS) and all(x['available'] for x in result),'approved_model_evidence_unavailable')
    return result

def main():
    need(os.geteuid()==0 and sys.argv[1:]==['--approved-web-only-security-update'],'explicit_approved_sudo_mode_required')
    os.umask(0o077);source=Path(__file__).resolve().parent
    data=(source/'release_helpers.py').read_bytes();need(sha(data)==HELPER_SHA,'reviewed_helper_checksum_mismatch')
    p=types.ModuleType('reviewed_release_helpers');p.__file__=str(source/'release_helpers.py')
    exec(compile(data,p.__file__,'exec'),p.__dict__);p.RELEASE=RELEASE
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'private_receipt_parent_required')
    need(RELEASE.resolve()==RELEASE and RELEASE.stat().st_uid==0 and not RELEASE.stat().st_mode&0o022,'trusted_release_directory_required')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'single_use_operation_already_consumed')
    need(OVERLAY.resolve()==OVERLAY and not OVERLAY.exists() and not OVERLAY.is_symlink(),'existing_overlay_must_not_be_overwritten')
    need(shutil.disk_usage('/var/lib/docker').free>=1000000000,'disk_reserve_required')
    available=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    need(available>=1000000000,'memory_reserve_required')
    # Hold the exact checksum-verified bytes; Docker never reopens a mutable source path.
    with (source/'security-candidate.tar').open('rb') as f:archive=f.read(ARCHIVE_SIZE+1)
    need(len(archive)==ARCHIVE_SIZE and sha(archive)==ARCHIVE_SHA,'candidate_archive_size_or_checksum_mismatch')
    rows=p.inventory();web=p.service(rows,'web');need(web['Image']==OLD,'production_image_drift')
    baseline=p.stable(rows,web['Id']);before=json.loads(p.compose(OLD_FILES,'config','--format','json'))
    original_env=sha(p.ENVFILE.read_bytes())
    key=Path('/etc/abap/credentials/advanced-assistant/openrouter-key');key_hash=sha(key.read_bytes())
    env=p.envmap(web['Config']['Env'])
    need(all(env.get(k)=='true' for k in ['ABAP_ADVANCED_ASSISTANT_ENABLED','ABAP_ASSISTANT_REMOTE_APPROVED','ABAP_ASSISTANT_DEMO_ONLY'])
         and env.get('ABAP_ASSISTANT_N8N_WORKFLOWS')=='' and env.get('ABAP_ASSISTANT_ALLOW_LOCAL_DEVELOPMENT')=='false'
         and env.get('ABAP_ASSISTANT_CLOUD_VALIDATION_FILE')=='/run/assistant-validation/cloud-validation.json','approved_synthetic_configuration_required')
    original_image=json.loads(p.docker('image','inspect',OLD))[0]
    expected={**p.envmap(original_image['Config'].get('Env',[])),
              **{k:str(v) for k,v in before['services']['web']['environment'].items()}}
    need(env==expected,'compose_runtime_environment_drift')
    existing=p.docker('image','ls','--no-trunc','--quiet',TAG).decode().split()
    need(not existing or existing==[NEW],'existing_candidate_tag_must_not_be_overwritten')
    rag=b'public-rag-chat.js' in p.http('/login')[1]
    report={'operation':'approved-web-security-image-20261104-1','status':'running','stage':'load_security_image',
            'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'migrations_run':False,'credentials_changed':False,'timers_changed':False,'b2_requests':0,
            'baseline':p.baseline_smoke(rag),'baseline_models':models(p,web['Id'])}
    checkpoint(report,first=True);installed=False;web_changed=False
    try:
        if not existing:p.docker('load',data=archive,timeout=180)
        del archive
        candidate=json.loads(p.docker('image','inspect',TAG))[0]
        need(candidate['Id']==NEW and candidate['Config']==original_image['Config'],'candidate_identity_or_runtime_configuration_mismatch')
        need(candidate['RootFS']['Layers'][:len(original_image['RootFS']['Layers'])]==original_image['RootFS']['Layers'],'candidate_base_layers_changed')
        p.write_new(OVERLAY,OVERLAY_BYTES,0o640);installed=True
        files=OLD_FILES+[str(OVERLAY)];after=json.loads(p.compose(files,'config','--format','json'));image_only(before,after)
        report['stage']='replace_web_only';checkpoint(report);web_changed=True
        p.compose(files,'up','-d','--no-deps','--no-build','--pull','never','web',timeout=120)
        current=p.service(p.inventory(),'web');need(current['Image']==NEW,'deployed_image_mismatch')
        need(p.envmap(current['Config']['Env'])==env,'runtime_environment_changed')
        need(current['HostConfig']==web['HostConfig'],'web_runtime_configuration_changed')
        fields=['Type','Name','Source','Destination','RW','Propagation']
        mounts=lambda row:sorted(json.dumps({k:v.get(k) for k in fields},sort_keys=True) for v in row['Mounts'])
        need(mounts(current)==mounts(web),'web_mounts_changed')
        report['smoke']=p.baseline_smoke(rag);report['models']=models(p,current['Id'])
        need(p.stable(p.inventory(),current['Id'])==baseline,'other_production_container_changed')
        need(sha(p.ENVFILE.read_bytes())==original_env and sha(key.read_bytes())==key_hash,'environment_or_credential_file_changed')
        report.update(status='PASS-web-only-security-update',stage='complete',image_id=NEW,
                      other_containers_preserved=True,original_environment_preserved=True,key_preserved=True)
    except BaseException as error:
        for name in ['SIGINT','SIGTERM','SIGHUP']:
            if hasattr(signal,name):signal.signal(getattr(signal,name),signal.SIG_IGN)
        report.update(status='FAIL-security-update',failure={'stage':report['stage'],
            'code':str(error) if isinstance(error,(Stop,p.Stop)) else 'operation_error_suppressed'})
        rollback=[]
        if web_changed:
            try:
                p.compose(OLD_FILES,'up','-d','--no-deps','--no-build','--pull','never','web',timeout=120)
                need(p.service(p.inventory(),'web')['Image']==OLD,'rollback_image_mismatch')
                report['rollback_smoke']=p.baseline_smoke(rag)
            except BaseException:rollback.append('web_rollback_blocked')
        if installed and not rollback:
            try:
                need(not OVERLAY.is_symlink() and sha(OVERLAY.read_bytes())==sha(OVERLAY_BYTES),'owned_overlay_changed')
                OVERLAY.unlink() # Only this invocation's new image overlay, never prior config.
            except BaseException:rollback.append('owned_overlay_cleanup_blocked')
        report['rollback']={'status':'PASS' if not rollback else 'BLOCKED','errors':rollback}
    finally:
        report['completed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();checkpoint(report)
    return report

if __name__=='__main__':
    def interrupted(signum,frame):raise Stop('operator_interrupted')
    for name in ['SIGTERM','SIGHUP']:
        if hasattr(signal,name):signal.signal(getattr(signal,name),interrupted)
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-before-update','code':str(error) if isinstance(error,Stop) else 'precondition_unavailable'}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('status')=='PASS-web-only-security-update' else 1)
