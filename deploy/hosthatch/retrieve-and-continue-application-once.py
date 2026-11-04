#!/usr/bin/env python3
"""Approved two-file retrieval plus one offline continuation; fail closed on quotas."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid

ROOT=Path('/var/backups/abap')
PRODUCTION_IMAGE='sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49'
RECEIPT=ROOT/'approved-targeted-app-recovery-20261104-1.json'
NOT_BEFORE=dt.datetime(2026,11,4,tzinfo=dt.timezone.utc)
DEPENDENCIES_SHA='6adac20c7e27b0692cbad2284865d93b86bd39ef76f4bb25f647097f993d3c26'
FILES=[('application-configuration.tar','a6cf741f6bc5cdeaf0016b698bf77b0f651ffbb521c760796869418953a5a848',
 '/application-configuration.tar',61440,'2281312dbb691abe693dfb2467361e951624c840654c126bbe64958c76e5d0d8'),
 ('database.dump','ac2dae86ca8f5106bfcb4c08a57aa8e1afec77496ab0cfb3e010fd087cd55e45',
 '/var/backups/abap/staging/database.dump',72058,'25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761')]
ENV={'PATH':'/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/nonexistent','LC_ALL':'C','GOMAXPROCS':'1','GOMEMLIMIT':'256MiB'}
class Guard(Exception):pass
def need(value,code):
    if not value:raise Guard(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def read_bounded(path,limit):
    with path.open('rb') as f:data=f.read(limit+1)
    need(len(data)<=limit,'review_input_size_limit');return data
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def quota_gate(proof,now):
    need(now>=NOT_BEFORE,'daily_reset_not_reached_no_retrieval')
    need(proof.get('source') in {'operator_backblaze_caps_alerts','authenticated_backblaze_caps_alerts'} and proof.get('caps_unchanged') is True,'provider_allowance_confirmation_required')
    checked=dt.datetime.fromisoformat(str(proof.get('checked_at_utc','')).replace('Z','+00:00'))
    need(checked.tzinfo is not None and proof.get('utc_day')==now.date().isoformat() and 0<=(now-checked).total_seconds()<=900,'provider_allowance_confirmation_stale')
    for key,minimum in [('class_b_remaining',1000),('class_c_remaining',500),('download_remaining_bytes',104857600)]:
        need(type(proof.get(key)) is int and proof[key]>=minimum,'provider_allowance_insufficient')
    status='PASS-operator-confirmed' if proof['source']=='operator_backblaze_caps_alerts' else 'PASS-authenticated-console-observed'
    return {'status':status,'utc_day':proof['utc_day'],'class_b_remaining':proof['class_b_remaining'],
        'class_c_remaining':proof['class_c_remaining'],'download_remaining_bytes':proof['download_remaining_bytes'],'caps_changed':False}
def error_category(raw):
    text=raw[:65536].decode('utf-8','replace').lower()
    for code,markers in [('quota_or_cap',['cap_exceeded','transaction cap','usage cap','quota','status code: 429']),
        ('authorization',['accessdenied','unauthorized','invalidaccesskeyid','signaturedoesnotmatch']),
        ('not_found',['not found','nosuchkey','no matching id']),('connection',['connection refused','no such host','tls handshake']),
        ('integrity',['ciphertext verification','decrypt','checksum mismatch'])]:
        if any(x in text for x in markers):return code
    return 'unclassified'
def retrieve(p,entry,deadline):
    name,snapshot,path,size,expected=entry
    need(entry in FILES,'unapproved_remote_file')
    need(time.monotonic()<deadline,'targeted_retrieval_deadline')
    # The installed repository is S3-compatible B2. This fixed shell reads only
    # existing configuration/credentials; no value is passed on command arguments.
    code=('set -Eeuo pipefail; source "$1"; shift; operations_load_config; operations_configure_restic; '
        '[[ "$RESTIC_REPOSITORY" == s3:https://*.backblazeb2.com/* ]]; '
        '[[ "$RESTIC_CACHE_DIR" == /var/cache/abap-restic ]]; '
        'exec "$@"')
    args=['/bin/bash','--noprofile','--norc','-c',code,'approved-targeted-read',str(p.LIB),str(p.RESTIC),
        '--no-lock','--cache-dir','/var/cache/abap-restic','--limit-download','256',
        '-o','s3.connections=1','-o','s3.retries=0','dump',snapshot,path]
    process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV,start_new_session=True)
    output=bytearray();errors=bytearray();overflow=threading.Event()
    def reader(stream,target,limit,fail=False):
        try:
            while True:
                chunk=stream.read(8192)
                if not chunk:break
                room=max(0,limit-len(target));target.extend(chunk[:room])
                if fail and len(chunk)>room:overflow.set();break
        finally:stream.close()
    threads=[threading.Thread(target=reader,args=(process.stdout,output,size+1,True),daemon=True),
        threading.Thread(target=reader,args=(process.stderr,errors,65536),daemon=True)]
    for thread in threads:thread.start()
    try:
        while process.poll() is None:
            need(not overflow.is_set(),'retrieved_output_size_exceeded')
            need(time.monotonic()<deadline,'targeted_retrieval_deadline')
            time.sleep(.1)
        for thread in threads:thread.join(timeout=5)
        need(not any(t.is_alive() for t in threads),'retrieval_pipe_drain_failed')
        if process.returncode:
            e=Guard('targeted_read_failed');e.diagnostic={'exit_code':process.returncode,'stderr_category':error_category(bytes(errors))};raise e
        need(len(output)==size and sha(output)==expected,'retrieved_size_or_sha256_mismatch')
        return bytes(output)
    finally:
        if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
        for thread in threads:thread.join(timeout=5)
def mount_identity(path):
    rows=[l.split() for l in Path('/proc/self/mountinfo').read_text().splitlines() if l.split()[4]==str(path)]
    need(len(rows)==1 and rows[0][rows[0].index('-')+1]=='tmpfs','temporary_ram_mount_identity_failed')
    return rows[0][0],rows[0][2]
def owned(root,ident):
    s=root.lstat();need(root.parent==ROOT and root.name.startswith('recovery-inputs-') and root.resolve()==root and s.st_uid==0
        and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==0o700 and (s.st_dev,s.st_ino)==ident,'temporary_directory_identity_failed')
def main():
    need(os.geteuid()==0 and len(sys.argv)==1,'authenticated_sudo_no_arguments_required')
    now=dt.datetime.now(dt.timezone.utc);need(now>=NOT_BEFORE,'daily_reset_not_reached_no_retrieval')
    siblings=Path(__file__).resolve().parent
    proof_raw=read_bounded(siblings/'quota-confirmation.json',8192)
    need(sha(proof_raw)==globals().get('__quota_confirmation_sha256__'),'provider_allowance_confirmation_digest_missing_or_mismatch')
    proof=json.loads(proof_raw);quota=quota_gate(proof,now)
    raw=read_bounded(siblings/'dependencies.json',65536);need(sha(raw)==DEPENDENCIES_SHA,'dependency_manifest_digest_mismatch')
    dependencies=json.loads(raw);blobs={}
    for name,expected in dependencies.items():
        need(Path(name).name==name and name.endswith('.py'),'unsafe_dependency_name')
        blobs[name]=read_bounded(siblings/name,262144);need(sha(blobs[name])==expected,'reviewed_dependency_digest_mismatch')
    # Import the already hashed bytes, avoiding a second read of user-owned files.
    import types
    def frozen(name,module_name):
        m=types.ModuleType(module_name);m.__file__=str(siblings/name);exec(compile(blobs[name],m.__file__,'exec'),m.__dict__);return m
    p=frozen('preserve-current-app-once.py','verifier_for_retrieval');p.DEADLINE=time.monotonic()+1800
    os.umask(0o077);os.nice(15)
    need(ROOT.resolve()==ROOT and ROOT.is_dir() and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'unsafe_receipt_parent')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'approved_operation_already_consumed')
    for path,private in [(p.LIB,False),(p.RESTIC,False),(Path('/etc/abap/operations.conf'),True)]:p.trusted(path,private)
    cache=Path('/var/cache/abap-restic');need(cache.resolve()==cache and cache.is_dir() and cache.stat().st_uid==0 and not cache.stat().st_mode&0o077,'existing_cache_not_private')
    before,rows=p.inventory();need(p.service(rows,'web')['Image']==PRODUCTION_IMAGE and p.service(rows,'database')['Image']==p.DB_IMAGE,'production_image_drift')
    need(not (ROOT/'approved-offline-app-continuation-20261104-1.json').exists(),'offline_continuation_already_consumed')
    need(__import__('shutil').disk_usage(ROOT).free>=8000000000,'insufficient_disk_reserve')
    mem=next(int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))
    need(mem>=2000000000,'insufficient_memory_reserve')
    result={'operation':'approved-targeted-app-recovery-20261104-1','status':'RUNNING','stage':'temporary_input_storage','quota_confirmation':quota,
        'targeted_retrieval':'BLOCKED-not-completed','artifact_integrity':'BLOCKED-not-completed','retrieval_invocations':0,'artifacts':[]}
    def checkpoint():
        data=json.dumps(result,indent=2).encode();temp=RECEIPT.with_name(RECEIPT.name+'.next')
        with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600),'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temp,RECEIPT)
    with os.fdopen(os.open(RECEIPT,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(json.dumps(result).encode())
    root=ROOT/('recovery-inputs-'+uuid.uuid4().hex[:16]);ident=None
    mounted=False;mount=None;cleanup=[];started=time.monotonic()
    try:
        root.mkdir(mode=0o700);s=root.stat();ident=(s.st_dev,s.st_ino)
        result['input_directory']=str(root);result['original_directory_identity']=ident;checkpoint()
        p.call(['/usr/bin/mount','-t','tmpfs','-o','size=1m,mode=0700,nodev,nosuid,noexec','tmpfs',str(root)],timeout=20)
        mounted=True;mount=mount_identity(root)
        deadline=time.monotonic()+300
        for entry in FILES:
            result['stage']='retrieve_configuration' if entry[0]=='application-configuration.tar' else 'retrieve_database_dump'
            result['retrieval_invocations']+=1;checkpoint()
            data=retrieve(p,entry,deadline)
            with os.fdopen(os.open(root/entry[0],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(data)
            result['artifacts'].append({'name':entry[0],'snapshot_id':entry[1],'bytes':len(data),'sha256':sha(data),'status':'PASS'})
            checkpoint()
        result['targeted_retrieval']='PASS';result['artifact_integrity']='PASS';result['stage']='offline_application_recovery';checkpoint()
        bundle=root/'bundle';bundle.mkdir(mode=0o700)
        for name,data in blobs.items():
            with os.fdopen(os.open(bundle/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o500),'wb') as f:f.write(data)
        offline=load(bundle/'continue-current-application-offline.py','approved_offline_continuation')
        previous=sys.argv[:];sys.argv=[str(bundle/'continue-current-application-offline.py'),'--execute-approved-continuation']
        try:result['recovery']=offline.main()
        finally:sys.argv=previous
        result['status']='PASS-targeted-retrieval-and-application-recovery' if result['recovery'].get('status')=='PASS-isolated-current-application-rehearsal' else 'FAIL-or-BLOCKED-application-recovery'
    except BaseException as error:
        result['status']='FAIL-or-BLOCKED-targeted-operation'
        result['failure']={'stage':result['stage'],'code':str(error) if isinstance(error,Guard) else getattr(error,'safe_code','internal_error')}
        if hasattr(error,'diagnostic'):result['failure']['diagnostic']=error.diagnostic
    finally:
        p.DEADLINE=time.monotonic()+120 # Cleanup and postflight have an independent allowance.
        saved=True
        continuation_receipt=ROOT/'approved-offline-app-continuation-20261104-1.json'
        if 'recovery' not in result and continuation_receipt.exists():
            try:result['recovery']=json.loads(continuation_receipt.read_bytes())
            except BaseException:cleanup.append('offline_result_unavailable')
        try:checkpoint()
        except BaseException:saved=False;cleanup.append('report_checkpoint_failed')
        recovery_safe='recovery' not in result or result['recovery'].get('cleanup',{}).get('status')=='PASS'
        if not recovery_safe:cleanup.append('input_storage_preserved_until_offline_cleanup_resolved')
        if mounted and saved and recovery_safe:
            try:
                need(mount_identity(root)==mount,'ram_mount_changed');p.call(['/usr/bin/umount',str(root)],timeout=30);mounted=False
            except BaseException:cleanup.append('owned_ram_unmount_blocked')
        if not mounted and saved and ident is not None:
            try:owned(root,ident);root.rmdir()
            except BaseException:cleanup.append('empty_owned_directory_cleanup_blocked')
        elif ident is None and root.exists():cleanup.append('created_directory_identity_unavailable')
        result['input_cleanup']={'status':'PASS' if not cleanup else 'BLOCKED','errors':cleanup}
        try:result['production_state_preservation']={'status':'PASS' if p.inventory()[0]==before else 'FAIL'}
        except BaseException:result['production_state_preservation']={'status':'BLOCKED'}
        if cleanup or result['production_state_preservation']['status']!='PASS':result['status']='BLOCKED-safety-or-cleanup'
        result['duration_seconds']=round(time.monotonic()-started,3);checkpoint()
    return result
if __name__=='__main__':
    def interrupted(signum,frame):raise Guard('operator_interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    try:answer=main()
    except BaseException as error:answer={'status':'BLOCKED-before-retrieval','failure_code':str(error) if isinstance(error,Guard) else 'precondition_unavailable','retrieval_invocations':0}
    print(json.dumps(answer,indent=2));raise SystemExit(0 if answer.get('status')=='PASS-targeted-retrieval-and-application-recovery' else 1)
