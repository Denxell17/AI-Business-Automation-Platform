#!/usr/bin/env python3
"""Explicitly approved two-file installation only; no jobs or timer/service edits."""
import ast
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import types
import uuid

ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-n8n-recurring-staging-install-20261104-1.json'
FILES={
 'n8n-backup.sh':('/usr/local/sbin/n8n-backup','c74d735da88a11278f7ea3e4537e4f6a4364720f3294920dbf97ea76ad8546e3','9fd130ea7fd55d07219c8ea6fd51b30647d0e5aa851749b02e2e3e8f87159077'),
 'n8n_backup_state.py':('/usr/local/lib/abap/n8n_backup_state.py','f6477ee46a97ca1737bd0c236adc7cf08105f7eddc946c026fb7d581a3a74462','1f53303333b264cbc6c3d884ca8fc67155952465e8544909543dbd3359643808')}
DIAG_SHA='4306de307731a5e9ac9d6403bebbb9da1f7776588fc3685393230ef57f093746'
class Stop(Exception):pass
def need(v,code):
    if not v:raise Stop(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def read_trusted(path):
    s=path.lstat()
    parent=path.parent.stat()
    need(parent.st_uid==0 and not parent.st_mode&0o022,'untrusted_install_directory')
    need(path.resolve()==path and stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022 and s.st_size<131072,'untrusted_installed_file')
    return path.read_bytes(),s
def call(args):
    p=subprocess.run(args,capture_output=True,timeout=30,env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LC_ALL':'C'})
    need(p.returncode==0,'bounded_validation_failed');return p.stdout
def write_new(path,data,mode):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as stream:
        os.fchmod(stream.fileno(),mode);stream.write(data);stream.flush();os.fsync(stream.fileno())
def replace(path,data,s):
    temporary=path.parent/('.n8n-reviewed-'+uuid.uuid4().hex)
    try:
        write_new(temporary,data,stat.S_IMODE(s.st_mode));os.chown(temporary,s.st_uid,s.st_gid)
        os.replace(temporary,path)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if temporary.exists():temporary.unlink()
def units():
    result={}
    for name in ['n8n-backup.service','n8n-backup.timer']:
        raw=call(['/usr/bin/systemctl','show',name,'--no-pager','-p','ActiveState','-p','UnitFileState',
            '-p','ExecStart','-p','ExecStopPost','-p','FragmentPath','-p','DropInPaths'])
        fields=dict(line.split('=',1) for line in raw.decode().splitlines() if '=' in line)
        need(fields.get('ActiveState') in {'failed','inactive'} and fields.get('UnitFileState')=='disabled','backup_service_or_timer_not_quiescent')
        if name.endswith('.service'):
            need('path=/usr/local/sbin/n8n-backup ' in fields.get('ExecStart','') and
                 'path=/usr/local/sbin/n8n-ensure-running ' in fields.get('ExecStopPost',''),'production_backup_unit_identity_changed')
        result[name]=sha(raw)
    return result
def staging_identity():
    path=Path('/var/backups/n8n/staging');s=path.lstat()
    need(path.resolve()==path and stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'protected_staging_identity_unavailable')
    return (s.st_dev,s.st_ino,sha(json.dumps(sorted(p.name for p in path.iterdir())).encode()))
def restore_originals(changed,previous,metadata):
    failures=[]
    for name in reversed(changed):
        try:
            replace(Path(FILES[name][0]),previous[name],metadata[name])
            need(sha(Path(FILES[name][0]).read_bytes())==FILES[name][1],'rollback_hash_failed')
        except BaseException:failures.append('original_restore_failed')
    return failures
def receipt(report):
    # Already reserved exclusively; never follow a substituted path.
    with os.fdopen(os.open(RECEIPT,os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW),'w') as f:
        json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
def main():
    need(os.geteuid()==0 and sys.argv[1:]==['--approved-install-only'],'explicit_authenticated_install_approval_required')
    os.umask(0o077)
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'private_backup_parent_required')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'single_use_operation_consumed')
    source=Path(__file__).resolve().parent
    raw=(source/'diagnose-existing-postgresql-restore.py').read_bytes();need(sha(raw)==DIAG_SHA,'reviewed_inventory_helper_mismatch')
    diag=types.ModuleType('reviewed_diag');diag.__file__=str(source/'diagnose-existing-postgresql-restore.py')
    exec(compile(raw,diag.__file__,'exec'),diag.__dict__)
    lock=os.open('/run/lock/abap-production-backup.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    with os.fdopen(lock,'w'):
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        previous={};candidates={};metadata={}
        for name,(destination,old,new) in FILES.items():
            path=Path(destination);data,s=read_trusted(path)
            need(sha(data)==old,'installed_source_drift')
            candidate=(source/name).read_bytes();need(sha(candidate)==new,'reviewed_candidate_mismatch')
            previous[name]=data;candidates[name]=candidate;metadata[name]=s
        ast.parse(candidates['n8n_backup_state.py'])
        p=subprocess.run(['/bin/bash','-n'],input=candidates['n8n-backup.sh'],capture_output=True,timeout=10)
        need(p.returncode==0,'candidate_shell_syntax_failed')
        unit_before=units();staging_before=staging_identity();baseline=diag.inventory()
        webids=diag.docker('ps','-q','--filter','label=com.docker.compose.project=abap-deploy','--filter','label=com.docker.compose.service=web').stdout.decode().split()
        need(len(webids)==1,'production_web_ambiguous')
        web=json.loads(diag.docker('inspect',webids[0]).stdout)[0]
        need(web['Image']=='sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c','current_production_image_changed')
        need(diag.shutil.disk_usage(ROOT).free>100000000,'backup_copy_capacity_required')
        backup=ROOT/('n8n-recurring-before-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
        backup.mkdir(mode=0o700)
        for name in FILES:
            write_new(backup/(name+'.before'),previous[name],0o600)
            need(sha((backup/(name+'.before')).read_bytes())==FILES[name][1],'original_copy_verification_failed')
            write_new(backup/(name+'.reviewed'),candidates[name],0o500)
        write_new(backup/'preservation.json',json.dumps({name:{'sha256':FILES[name][1],'uid':metadata[name].st_uid,
            'gid':metadata[name].st_gid,'mode':oct(stat.S_IMODE(metadata[name].st_mode))} for name in FILES},indent=2).encode(),0o600)
        # Check the exact protected candidate before replacement; no capture/SQLite write.
        call(['/usr/bin/python3','-I','-B',str(backup/'n8n_backup_state.py.reviewed'),'check'])
        report={'operation':'approved-n8n-recurring-staging-install-20261104-1','status':'running',
            'originals_directory':str(backup),'originals_verified_before_replacement':True,
            'backup_jobs_run':0,'repository_requests':0,'timers_changed':False,'services_restarted':False}
        write_new(RECEIPT,json.dumps(report).encode(),0o600);changed=[]
        try:
            for name,(destination,old,new) in FILES.items():
                # Include a target before replacement so even a post-rename fsync failure rolls back.
                changed.append(name);replace(Path(destination),candidates[name],metadata[name])
                actual,s=read_trusted(Path(destination))
                need(sha(actual)==new and (s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))==
                     (metadata[name].st_uid,metadata[name].st_gid,stat.S_IMODE(metadata[name].st_mode)),'installed_integrity_failed')
            call(['/bin/bash','-n','/usr/local/sbin/n8n-backup'])
            call(['/usr/bin/python3','-I','-B','/usr/local/lib/abap/n8n_backup_state.py','check'])
            need(units()==unit_before and staging_identity()==staging_before and diag.inventory()==baseline,'protected_production_state_changed')
            report.update(status='PASS-two-files-installed-timer-still-disabled',installed_sha256={v[0]:v[2] for v in FILES.values()},
                original_staging_preserved=True,production_state_preservation='PASS',unit_configuration_preserved=True)
            receipt(report)
        except BaseException as error:
            for name in ['SIGINT','SIGTERM','SIGHUP']:
                if hasattr(signal,name):signal.signal(getattr(signal,name),signal.SIG_IGN)
            failures=restore_originals(changed,previous,metadata)
            report.update(status='FAIL-installation-rolled-back' if not failures else 'BLOCKED-file-rollback',
                failure=str(error) if isinstance(error,Stop) else 'installation_failure_suppressed',rollback_errors=failures)
            try:receipt(report)
            except BaseException:report['receipt_write_failed']=True
        return report
if __name__=='__main__':
    def interrupted(*_):raise Stop('operator_interrupted')
    for name in ['SIGTERM','SIGHUP']:
        if hasattr(signal,name):signal.signal(getattr(signal,name),interrupted)
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-before-install','code':str(error) if isinstance(error,Stop) else 'prerequisite_unavailable'}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('PASS') else 1)
