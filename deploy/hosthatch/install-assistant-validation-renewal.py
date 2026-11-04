#!/usr/bin/env python3
"""One approved installation: renewal job/timer and web-only proof directory bind."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-assistant-renewal-install-20261104-1.json'
RELEASE=Path('/opt/abap-advanced-assistant/releases/20261104-r2')
OVERLAY=RELEASE/'validation-renewal.json'
SCRIPT=Path('/usr/local/lib/abap/renew-assistant-model-validation.py')
SERVICE=Path('/etc/systemd/system/abap-assistant-validation.service')
TIMER=Path('/etc/systemd/system/abap-assistant-validation.timer')
KEY=Path('/etc/abap/credentials/advanced-assistant/openrouter-key')
PROOF=KEY.parent/'cloud-validation.json'
IMAGE='sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49'
MODELS=['openrouter:nvidia/nemotron-3.5-lightning:free','openrouter:cohere/north-mini-code:free']
class Stop(Exception):pass
def need(value,code):
    if not value:raise Stop(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path,limit=262144):
    with path.open('rb') as f:data=f.read(limit+1)
    need(len(data)<=limit,'review_input_size_limit');return data
def save(result):
    data=json.dumps(result,indent=2).encode();need(len(data)<131072,'receipt_size_limit')
    temp=RECEIPT.with_name(RECEIPT.name+'.next')
    with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600),'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(temp,RECEIPT)
def verify_delta(before,after):
    need(all(before.get(k)==after.get(k) for k in set(before)|set(after) if k!='services'),'project_configuration_changed')
    a=before['services'];b=after['services'];need(set(a)==set(b) and all(v==b.get(k) for k,v in a.items() if k!='web'),'unrelated_service_configuration_changed')
    a=a['web'];b=b['web'];need(all(a.get(k)==b.get(k) for k in set(a)|set(b) if k not in ['environment','volumes']),'web_configuration_changed')
    ae=a['environment'];be=b['environment'];changed={k for k in set(ae)|set(be) if ae.get(k)!=be.get(k)}
    need(changed=={'ABAP_ASSISTANT_CLOUD_VALIDATION_FILE'} and be['ABAP_ASSISTANT_CLOUD_VALIDATION_FILE']=='/run/assistant-validation/cloud-validation.json','unexpected_environment_change')
    need(all(v in b['volumes'] for v in a['volumes']),'existing_mount_changed')
    extra=[v for v in b['volumes'] if v not in a['volumes']]
    need(len(extra)==1 and extra[0].get('type')=='bind' and extra[0].get('source')==str(KEY.parent) and
        extra[0].get('target')=='/run/assistant-validation' and extra[0].get('read_only') is True and
        extra[0].get('bind',{}).get('create_host_path') is False,'unexpected_mount_change')
def unit_state(p,unit):
    raw=p.call('/usr/bin/systemctl','show',unit,'-p','ActiveState','-p','UnitFileState','-p','Result','-p','ExecMainStatus','-p','NextElapseUSecRealtime','--no-pager').decode()
    return dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
def main():
    need(os.geteuid()==0 and len(sys.argv)==1,'authenticated_sudo_required');os.umask(0o077)
    source=Path(__file__).resolve().parent;raw=read(source/'renewal-install-inputs.json')
    need(sha(raw)==globals().get('__manifest_sha256__'),'install_manifest_mismatch');manifest=json.loads(raw)
    blobs={}
    for name,h in manifest['files'].items():
        need(Path(name).name==name,'unsafe_input_filename');blobs[name]=read(source/name);need(sha(blobs[name])==h,'input_checksum_mismatch')
    p=types.ModuleType('reviewed_release_helpers');p.__file__=str(source/'release_helpers.py')
    exec(compile(blobs['release_helpers.py'],p.__file__,'exec'),p.__dict__);p.RELEASE=RELEASE
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'unsafe_receipt_parent')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'installation_already_reserved_do_not_repeat')
    targets={SCRIPT:('renew-assistant-model-validation.py',0o750),SERVICE:('abap-assistant-validation.service',0o644),
        TIMER:('abap-assistant-validation.timer',0o644),OVERLAY:('compose.assistant-validation-renewal.json',0o640)}
    need(all(not path.exists() and not path.is_symlink() and path.resolve()==path and path.parent.is_dir() for path in targets),'installation_target_exists_or_is_unsafe')
    rows=p.inventory();web=p.service(rows,'web');need(web['Image']==IMAGE,'running_image_drift')
    old_files=['disabled-web.json','activation-web.json'];new_files=old_files+[str(OVERLAY)]
    baseline=p.stable(rows,web['Id']);environment_digest=sha(p.ENVFILE.read_bytes());key_digest=sha(read(KEY,4096));proof_before=sha(read(PROOF))
    before=json.loads(p.compose(old_files,'config','--format','json'))
    actual=p.envmap(web['Config']['Env']);expected={**p.envmap(json.loads(p.docker('image','inspect',IMAGE))[0]['Config'].get('Env',[])),**{k:str(v) for k,v in before['services']['web']['environment'].items()}}
    need(actual==expected,'running_configuration_drift')
    need(actual.get('ABAP_ADVANCED_ASSISTANT_ENABLED')=='true' and actual.get('ABAP_ASSISTANT_REMOTE_APPROVED')=='true'
        and actual.get('ABAP_ASSISTANT_DEMO_ONLY')=='true' and actual.get('ABAP_ASSISTANT_N8N_WORKFLOWS')=='','approved_synthetic_mode_required')
    rag=b'public-rag-chat.js' in p.http('/login')[1];health=p.baseline_smoke(rag)
    result={'operation':'approved-assistant-renewal-install-20261104-1','status':'RUNNING','stage':'install_files',
        'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image_rebuilt':False,'migrations_run':False,
        'disaster_recovery_performed':False,'b2_requests':0,'baseline':health}
    p.write_new(RECEIPT,json.dumps(result).encode(),0o600)
    installed=[];reloaded=False;web_changed=False;service_started=False;timer_enabled=False
    try:
        for path,(name,mode) in targets.items():p.write_new(path,blobs[name],mode);installed.append(path)
        p.call('/usr/bin/systemd-analyze','--man=no','verify',str(SERVICE),str(TIMER))
        after=json.loads(p.compose(new_files,'config','--format','json'));verify_delta(before,after)
        result['stage']='recreate_web_only';save(result);web_changed=True
        p.compose(new_files,'up','-d','--no-deps','--no-build','--pull','never','web',timeout=120)
        current=p.service(p.inventory(),'web');need(current['Image']==IMAGE,'unchanged_image_not_preserved')
        result['web_smoke']=p.baseline_smoke(rag)
        result['stage']='verify_evidence_access';save(result)
        probe="""import hashlib,json,os,pathlib
from assistant_gateway import configured_models
p=pathlib.Path(os.environ['ABAP_ASSISTANT_CLOUD_VALIDATION_FILE'])
print(json.dumps({'path':str(p),'evidence_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'models':[{'id':m.id,'available':m.available} for m in configured_models()]}))
"""
        access=json.loads(p.docker('exec',current['Id'],'python','-B','-c',probe))
        need(access['path']=='/run/assistant-validation/cloud-validation.json' and access['evidence_sha256']==sha(read(PROOF))
            and sorted(m['id'] for m in access['models'])==sorted(MODELS),'evidence_access_verification_failed')
        result['evidence_access']='PASS'
        result['stage']='run_service_once';save(result)
        p.call('/usr/bin/systemctl','daemon-reload');reloaded=True
        since=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        service_started=True;p.call('/usr/bin/systemctl','start','abap-assistant-validation.service',timeout=240)
        result['service']=unit_state(p,'abap-assistant-validation.service')
        need(result['service'].get('Result')=='success' and result['service'].get('ExecMainStatus')=='0','renewal_service_failed')
        logs=p.call('/usr/bin/journalctl','-u','abap-assistant-validation.service','--since',since,'--no-pager','-o','json','-n','20')
        reports=[]
        for line in logs.decode('utf-8','replace').splitlines():
            try:
                message=json.loads(json.loads(line).get('MESSAGE',''))
                if isinstance(message,dict) and 'status' in message:reports.append(message)
            except (ValueError,TypeError):pass
        need(reports,'renewal_service_receipt_unavailable');report=reports[-1]
        need(str(report['status']).startswith(('PASS','SKIP')),'renewal_service_did_not_succeed')
        result['renewal_check']={k:report[k] for k in ['status','changed','requests','models'] if k in report}
        access=json.loads(p.docker('exec',current['Id'],'python','-B','-c',probe))
        need(access['evidence_sha256']==sha(read(PROOF)) and all(m['available'] for m in access['models']),'renewed_evidence_or_models_unavailable')
        result['models']=access['models'];result['proof_content_changed']=proof_before!=sha(read(PROOF))
        result['stage']='enable_hourly_timer';save(result)
        timer_enabled=True;p.call('/usr/bin/systemctl','enable','--now','abap-assistant-validation.timer')
        result['timer']=unit_state(p,'abap-assistant-validation.timer')
        need(result['timer'].get('ActiveState')=='active' and result['timer'].get('UnitFileState')=='enabled','hourly_timer_not_active')
        current=p.service(p.inventory(),'web')
        need(p.stable([r for r in p.inventory() if r['Id']!=current['Id']],None)==baseline,'unrelated_container_changed')
        need(sha(p.ENVFILE.read_bytes())==environment_digest and sha(read(KEY,4096))==key_digest,'original_configuration_or_key_changed')
        result.update(status='PASS-automatic-model-validation-renewal-installed',stage='complete',image_id=current['Image'],
            other_containers_preserved=True,original_environment_preserved=True,openrouter_key_preserved=True)
    except BaseException as error:
        result.update(status='FAIL-installation-stopped',failure={'stage':result['stage'],'code':str(error) if isinstance(error,(Stop,p.Stop)) else 'internal_error_suppressed'})
        rollback=[]
        if timer_enabled:
            try:p.call('/usr/bin/systemctl','disable','--now','abap-assistant-validation.timer')
            except BaseException:rollback.append('new_timer_disable_failed')
        if service_started:
            try:p.call('/usr/bin/systemctl','stop','abap-assistant-validation.service')
            except BaseException:rollback.append('new_service_stop_failed')
        if web_changed:
            try:p.compose(old_files,'up','-d','--no-deps','--no-build','--pull','never','web',timeout=120);result['rollback_web_smoke']=p.baseline_smoke(rag)
            except BaseException:rollback.append('original_web_configuration_restore_failed')
        for path in reversed(installed):
            try:
                name,_=targets[path];need(path.is_file() and not path.is_symlink() and sha(read(path))==manifest['files'][name],'installed_file_changed')
                # Preserve all supporting files if rollback is incomplete.
                if rollback:continue
                path.unlink()
            except BaseException:rollback.append('owned_installed_file_cleanup_blocked')
        if reloaded:
            try:p.call('/usr/bin/systemctl','daemon-reload')
            except BaseException:rollback.append('unit_reload_after_cleanup_failed')
        result['rollback']={'status':'PASS' if not rollback else 'BLOCKED','errors':rollback}
    finally:
        result['completed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(result)
    return result
if __name__=='__main__':
    import signal
    def interrupted(signum,frame):raise Stop('operator_interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-review-installation-receipt' if RECEIPT.exists() else 'BLOCKED-before-installation','code':str(error) if isinstance(error,Stop) else 'precondition_unavailable'}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('status','').startswith('PASS-automatic') else 1)
