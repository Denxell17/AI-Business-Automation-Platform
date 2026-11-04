#!/usr/bin/env python3
"""Approval required: enable existing timer; never manually dispatch a backup."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
import types

ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-n8n-recurring-timer-20261104-1.json'
EXPECTED={'/usr/local/sbin/n8n-backup':'9fd130ea7fd55d07219c8ea6fd51b30647d0e5aa851749b02e2e3e8f87159077',
 '/usr/local/lib/abap/n8n_backup_state.py':'1f53303333b264cbc6c3d884ca8fc67155952465e8544909543dbd3359643808'}
class Stop(Exception):pass
def need(value,code):
    if not value:raise Stop(code)
def call(*args):
    p=subprocess.run(args,capture_output=True,timeout=30,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
    need(p.returncode==0,'bounded_unit_operation_failed');return p.stdout.decode()
def show(name):
    return dict(line.split('=',1) for line in call('/usr/bin/systemctl','show',name,'--no-pager',
        '-p','ActiveState','-p','UnitFileState','-p','Result','-p','ExecMainStatus',
        '-p','ExecMainStartTimestampMonotonic','-p','InvocationID','-p','FragmentPath','-p','DropInPaths',
        '-p','NextElapseUSecRealtime','-p','ExecStart','-p','ExecStopPost').splitlines() if '=' in line)
def timer_contract(text):
    cfg=configparser.ConfigParser(interpolation=None);cfg.read_string(text)
    need(cfg.get('Timer','OnCalendar')=='*-*-* 05:30:00 UTC' and cfg.getboolean('Timer','Persistent')
         and cfg.get('Timer','Unit')=='n8n-backup.service','existing_timer_schedule_changed')
    need(set(cfg['Timer'])<={'oncalendar','persistent','accuracysec','unit'},'unexpected_timer_trigger')
def save(report,first=False):
    flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_EXCL if first else os.O_TRUNC)
    with os.fdopen(os.open(RECEIPT,flags,0o600),'w') as f:
        os.fchmod(f.fileno(),0o600);json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
def main():
    need(os.geteuid()==0 and sys.argv[1:]==['--approved-existing-timer'],'explicit_timer_activation_approval_required')
    os.umask(0o077)
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'private_receipt_parent_required')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'single_use_command_consumed')
    helper=Path(__file__).resolve().parent/'diagnose-existing-postgresql-restore.py';data=helper.read_bytes()
    need(hashlib.sha256(data).hexdigest()=='4306de307731a5e9ac9d6403bebbb9da1f7776588fc3685393230ef57f093746','reviewed_helper_mismatch')
    diag=types.ModuleType('reviewed_diag');exec(compile(data,str(helper),'exec'),diag.__dict__)
    for name,expected in EXPECTED.items():
        path=Path(name);s=path.lstat()
        need(path.resolve()==path and stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022
             and s.st_size<131072 and hashlib.sha256(path.read_bytes()).hexdigest()==expected,'installed_candidate_drift')
    before=show('n8n-backup.timer');service=show('n8n-backup.service')
    need(before['ActiveState']=='inactive' and before['UnitFileState']=='disabled' and not before['DropInPaths'],'timer_state_changed')
    need(service['ActiveState'] in {'inactive','failed'} and not service['DropInPaths']
         and 'path=/usr/local/sbin/n8n-backup ' in service['ExecStart']
         and 'path=/usr/local/sbin/n8n-ensure-running ' in service['ExecStopPost'],'backup_unit_state_changed')
    fragment=Path(before['FragmentPath']);s=fragment.lstat()
    need(fragment.resolve()==fragment and s.st_uid==0 and not s.st_mode&0o022 and s.st_size<8192,'untrusted_timer_fragment')
    content=fragment.read_bytes();timer_contract(content.decode())
    call('/usr/bin/python3','-I','-B','/usr/local/lib/abap/n8n_backup_state.py','check')
    baseline=diag.inventory()
    ids=diag.docker('ps','-q','--filter','label=com.docker.compose.project=abap-deploy','--filter','label=com.docker.compose.service=web').stdout.decode().split()
    need(len(ids)==1,'production_web_ambiguous')
    web=json.loads(diag.docker('inspect',ids[0]).stdout)[0]
    need(web['Image']=='sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c','production_web_image_changed')
    env=dict(v.split('=',1) for v in web['Config'].get('Env',[]))
    report={'operation':'approved-n8n-recurring-timer-20261104-1','status':'running',
        'manual_backup_dispatches':0,'direct_repository_requests':0,'workflow_dispatches':0,
        'demo_readiness':{'integrations_enabled':env.get('ABAP_INTEGRATIONS_ENABLED')=='true',
            'endpoint_configured':bool(env.get('ABAP_N8N_BASE_URL')),
            'outbound_key_configured':bool(env.get('ABAP_OUTBOUND_WEBHOOK_SECRET')),
            'inbound_key_configured':bool(env.get('ABAP_INBOUND_WEBHOOK_SECRET'))}}
    save(report,True);changed=False;started=int(time.time())
    try:
        changed=True;call('/usr/bin/systemctl','enable','--now','n8n-backup.timer')
        after=show('n8n-backup.timer')
        need(after['ActiveState']=='active' and after['UnitFileState']=='enabled' and bool(after['NextElapseUSecRealtime']),'timer_activation_not_verified')
        # Allow systemd to dispatch any existing overdue calendar event; never
        # issue a service start. If it runs, preserve the real service result.
        time.sleep(2);observed=show('n8n-backup.service')
        deadline=time.monotonic()+1920
        while observed['ActiveState'] in {'activating','active','deactivating'}:
            need(time.monotonic()<deadline,'scheduled_backup_observation_timeout')
            time.sleep(5);observed=show('n8n-backup.service')
        triggered=(observed['ExecMainStartTimestampMonotonic']!=service['ExecMainStartTimestampMonotonic']
                   or observed['InvocationID']!=service['InvocationID'])
        report['calendar_backup_observed']=triggered
        if triggered:
            need(observed['Result']=='success' and observed['ExecMainStatus']=='0','scheduled_backup_failed')
            journal=call('/usr/bin/journalctl','-u','n8n-backup.service','--since','@'+str(started),'-n','200','--no-pager','-o','cat')
            snapshots=dict(re.findall(r'N8N_SNAPSHOT_VERIFIED: target=(standalone|public-rag-production) id=([0-9a-f]{64})',journal))
            need(set(snapshots)=={'standalone','public-rag-production'},'scheduled_snapshot_receipts_unavailable')
            report['scheduled_snapshot_ids']=snapshots
            report['scheduled_backup_result']='PASS'
        else:report['scheduled_backup_result']='NOT-RUN-await-next-calendar-event'
        need(fragment.read_bytes()==content and diag.inventory()==baseline,'production_or_timer_configuration_changed')
        report.update(status='PASS-existing-timer-active',timer={'active':True,'enabled':True,
            'next':after['NextElapseUSecRealtime'],'calendar':'05:30 UTC daily'},production_state_preservation='PASS')
    except BaseException as error:
        for name in ['SIGINT','SIGTERM','SIGHUP']:
            if hasattr(signal,name):signal.signal(getattr(signal,name),signal.SIG_IGN)
        report.update(status='BLOCKED-timer-activation',failure=str(error) if isinstance(error,Stop) else 'operation_error_suppressed')
        if changed:
            try:
                call('/usr/bin/systemctl','disable','--now','n8n-backup.timer')
                report['timer_reverted_to_disabled']=True
            except BaseException:report['timer_reverted_to_disabled']=False
        # Stopping a timer never cancels a running backup. Its existing 30-minute
        # systemd timeout remains authoritative; never stop an application container.
    finally:
        try:report['production_state_preservation']='PASS' if diag.inventory()==baseline else 'FAIL'
        except BaseException:report['production_state_preservation']='BLOCKED'
        if report['production_state_preservation']!='PASS':
            report['status']='BLOCKED-production-comparison'
            if changed:
                try:
                    call('/usr/bin/systemctl','disable','--now','n8n-backup.timer');report['timer_reverted_to_disabled']=True
                except BaseException:report['timer_reverted_to_disabled']=False
        try:save(report)
        except BaseException:
            report['status']='BLOCKED-receipt-write'
            if changed:
                try:
                    call('/usr/bin/systemctl','disable','--now','n8n-backup.timer');report['timer_reverted_to_disabled']=True
                except BaseException:report['timer_reverted_to_disabled']=False
    return report
if __name__=='__main__':
    def interrupted(*_):raise Stop('operator_interrupted')
    for name in ['SIGTERM','SIGHUP']:
        if hasattr(signal,name):signal.signal(getattr(signal,name),interrupted)
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-before-activation','code':str(error) if isinstance(error,Stop) else 'prerequisite_unavailable'}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('PASS') else 1)
