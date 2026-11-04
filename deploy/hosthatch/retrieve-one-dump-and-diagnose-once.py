#!/usr/bin/env python3
"""One approved exact dump retrieval, durable private retention, one diagnostic."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import time
import types

ROOT=Path('/var/backups/abap')
CACHE=ROOT/'recovery-cache'
DEST=CACHE/'database.dump'
RECEIPT=ROOT/'approved-one-dump-diagnostic-20261104-1.json'
ENTRY=('database.dump','ac2dae86ca8f5106bfcb4c08a57aa8e1afec77496ab0cfb3e010fd087cd55e45',
       '/var/backups/abap/staging/database.dump',72058,
       '25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761')
SOURCES={
 'retrieve-and-continue-application-once.py':'a393aeef4386f190bb8d0940c1afe25b6425081576a3db9af3170d0dfa94e6e9',
 'diagnose-existing-postgresql-restore.py':'4306de307731a5e9ac9d6403bebbb9da1f7776588fc3685393230ef57f093746'}
class Stop(Exception):pass

def need(value,code):
    if not value:raise Stop(code)

def sha(data):return hashlib.sha256(data).hexdigest()

def frozen(path,expected,name):
    data=path.read_bytes();need(len(data)<=131072 and sha(data)==expected,'reviewed_source_mismatch')
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(data,str(path),'exec'),module.__dict__);return module

def private_directory(path):
    s=path.lstat()
    need(path.resolve()==path and stat.S_ISDIR(s.st_mode) and s.st_uid==0
         and stat.S_IMODE(s.st_mode)==0o700,'private_directory_required')

def existing_dump(d):
    if DEST.exists() or DEST.is_symlink():
        data=d.read_private(DEST,ENTRY[3])
        need(len(data)==ENTRY[3] and sha(data)==ENTRY[4],'existing_cache_file_mismatch_no_overwrite')
        return data
    return None

def retain(data):
    """Publish only a complete authenticated file; never overwrite prior artifacts."""
    need(len(data)==ENTRY[3] and sha(data)==ENTRY[4],'dump_size_or_checksum_mismatch')
    if not CACHE.exists():CACHE.mkdir(mode=0o700)
    private_directory(CACHE)
    fd,name=tempfile.mkstemp(prefix='.new-database-',dir=CACHE)
    original=os.fstat(fd)
    try:
        with os.fdopen(fd,'wb') as f:
            os.fchmod(f.fileno(),0o600);f.write(data);f.flush();os.fsync(f.fileno())
        # Link installation is exclusive: an existing destination is never replaced.
        os.link(name,DEST,follow_symlinks=False)
        directory=os.open(CACHE,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        s=os.lstat(name)
        need((s.st_dev,s.st_ino)==(original.st_dev,original.st_ino),'owned_temporary_file_identity_changed')
        os.unlink(name) # Only the newly created temporary name, never the retained dump.

def save(report,first=False):
    flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_EXCL if first else os.O_TRUNC)
    with os.fdopen(os.open(RECEIPT,flags,0o600),'w') as f:
        os.fchmod(f.fileno(),0o600);json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())

def perform(fetch,d,quota):
    private_directory(ROOT)
    if CACHE.exists() or CACHE.is_symlink():private_directory(CACHE)
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'approved_single_file_operation_already_consumed')
    need(not d.RECEIPT.exists() and not d.RECEIPT.is_symlink(),'restore_diagnostic_already_consumed')
    inspection,verified=d.inspect_existing()
    if inspection.get('actionable_restore_error_recovered'):
        return {'status':'PASS-existing-error-recovered','inspection':inspection,'retrieval_invocations':0,'restore_attempts':0}
    cached=existing_dump(d)
    # A matching existing offline copy is also reusable; no B2 call is then needed.
    if cached is None and verified:
        cached=d.read_private(verified[0],ENTRY[3])
        need(len(cached)==ENTRY[3] and sha(cached)==ENTRY[4],'existing_offline_copy_changed')
    quota_result=fetch.quota_gate(quota,datetime.datetime.now(datetime.timezone.utc)) if cached is None else 'not-needed-existing-verified-copy'
    image=json.loads(d.docker('image','inspect',d.IMAGE).stdout)[0]
    need(image['Id']==d.IMAGE,'cached_postgresql_image_required_no_import')
    need(shutil.disk_usage(ROOT).free>=1000000000,'insufficient_disk_reserve')
    available=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    need(available>=1500000000,'insufficient_memory_reserve')
    for path,private in [(Path('/usr/local/lib/abap/abap-operations-lib.sh'),False),
                          (Path('/usr/local/bin/restic'),False),(Path('/etc/abap/operations.conf'),True)]:
        s=path.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&(0o077 if private else 0o022),'untrusted_existing_backup_dependency')
    report={'operation':'approved-one-dump-diagnostic-20261104-1','status':'running',
            'stage':'verify_and_retain_dump','quota_confirmation':quota_result,'retrieval_invocations':0,
            'restore_attempts':0,'production_changes':False,'image_imports':0,'full_recovery':False}
    save(report,first=True)
    try:
        if cached is None:
            report['stage']='retrieve_exact_database_dump';report['retrieval_invocations']=1;save(report)
            fetch.FILES=[ENTRY] # Narrow the reviewed helper to this one approved object.
            helper=types.SimpleNamespace(LIB=Path('/usr/local/lib/abap/abap-operations-lib.sh'),RESTIC=Path('/usr/local/bin/restic'))
            cached=fetch.retrieve(helper,ENTRY,time.monotonic()+300)
        if not DEST.exists():retain(cached)
        need(existing_dump(d) is not None,'retained_verified_dump_required')
        report['retained_dump']={'path':str(DEST),'bytes':ENTRY[3],'sha256':ENTRY[4],
                                 'mode':'0600','parent_mode':'0700','retained_after_diagnostic':True}
        report['stage']='restore_only_diagnostic';save(report)
        previous=sys.argv[:];sys.argv=[d.__file__,'--approved-restore-if-local']
        try:answer=d.main()
        finally:sys.argv=previous
        report['diagnostic']=answer;report['restore_attempts']=answer.get('restore_attempts',0)
        report['status']='PASS-retrieval-and-restore-only-diagnostic' if answer['status'].startswith('PASS-') else 'FAIL-or-BLOCKED-restore-only-diagnostic'
    except BaseException as error:
        report['status']='FAIL-or-BLOCKED-single-file-operation'
        report['failure']={'stage':report['stage'],'code':str(error) if isinstance(error,(Stop,fetch.Guard,d.Stop)) else 'operation_error_suppressed'}
        if hasattr(error,'diagnostic'):report['failure']['diagnostic']=error.diagnostic
    finally:
        # Deliberately preserve the verified source on success AND failure.
        try:report['verified_dump_still_retained']=existing_dump(d) is not None
        except BaseException:report['verified_dump_still_retained']=False
        save(report)
    return report

def main():
    need(os.geteuid()==0 and len(sys.argv)==1,'authenticated_sudo_no_arguments_required');os.umask(0o077)
    base=Path(__file__).resolve().parent
    fetch=frozen(base/'retrieve-and-continue-application-once.py',SOURCES['retrieve-and-continue-application-once.py'],'approved_single_read_helper')
    d=frozen(base/'diagnose-existing-postgresql-restore.py',SOURCES['diagnose-existing-postgresql-restore.py'],'approved_restore_only_helper')
    raw=(base/'quota-confirmation.json').read_bytes()
    need(len(raw)<=8192 and sha(raw)==globals().get('__quota_confirmation_sha256__'),'allowance_proof_checksum_mismatch')
    return perform(fetch,d,json.loads(raw))

if __name__=='__main__':
    import signal
    def interrupted(signum,frame):raise Stop('operator_interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-before-retrieval','code':str(error) if isinstance(error,Stop) else 'prerequisite_unavailable','retrieval_invocations':0}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('status','').startswith('PASS-') else 1)
