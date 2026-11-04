#!/usr/bin/env python3
"""Explicitly approved restore-only diagnostic; no retrieval, image import or app."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import time
import uuid

ROOT = Path('/var/backups/abap')
IMAGE = 'sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280'
DUMP_SHA = '25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761'
DUMP_SIZE = 72058
RECEIPT = ROOT / 'approved-restore-only-diagnostic-20261104-1.json'
OLD_ROOT = ROOT / 'app-rehearsal-48e9caffbe3f4e7c'
PATHS = [ROOT/'recovery-inputs-88e983ac786f499d/database.dump',
         OLD_ROOT/'sensitive/database.dump', ROOT/'staging/database.dump',
         ROOT/'recovery-cache/database.dump']
LOGS = [OLD_ROOT/'sensitive/daemon.log', OLD_ROOT/'sensitive/progress.json',
        OLD_ROOT/'sensitive/result.json']
ENV = {'PATH':'/usr/bin:/bin', 'HOME':'/nonexistent', 'LC_ALL':'C'}
PATTERNS = [
 ('connection_failure', r'connection to server|could not connect to server'),
 ('server_disconnected', r'server closed the connection|server closed connection'),
 ('server_starting', r'database system is starting up|database system is shutting down'),
 ('database_missing', r'database "[^"\n]*" does not exist'),
 ('role_missing', r'role "[^"\n]*" does not exist'),
 ('authentication_failure', r'password authentication failed|no password supplied'),
 ('unsupported_archive_version', r'unsupported version.*file header'),
 ('unrecognized_setting', r'unrecognized configuration parameter'),
 ('permission_denied', r'permission denied|must be owner|must be superuser'),
 ('duplicate_object', r'already exists|duplicate key'),
 ('missing_relation', r'(?:relation|schema|type|function) .*does not exist'),
 ('constraint_failure', r'violates .*constraint|foreign key constraint'),
 ('archive_truncated', r'unexpected end of file|input file is too short|could not read from input'),
 ('disk_full', r'no space left on device'),
 ('query_execution_failure', r'could not execute query'),
]

class Stop(Exception): pass

def need(value, code):
    if not value: raise Stop(code)

def sanitize(raw):
    """Only fixed categories/SQLSTATE/statement verbs escape private memory."""
    text = raw[:131072].decode('utf-8', 'replace')
    categories = [name for name, pattern in PATTERNS if re.search(pattern, text, re.I)]
    states = sorted(set(re.findall(r'\b(?:ERROR|FATAL|PANIC):\s+([0-9A-Z]{5}):|SQLSTATE[=: ]+([0-9A-Z]{5})\b', text)))
    states = sorted({part for pair in states for part in pair if part})[:8]
    statement = re.search(r'Command was:\s*(CREATE|ALTER|COPY|INSERT|SET|COMMENT|GRANT|REVOKE|SELECT|DROP)\b', text, re.I)
    return {'categories':categories or ['unclassified_postgresql_error'], 'sqlstates':states,
            'statement_type':statement[1].upper() if statement else None,
            'stderr_bytes':len(raw), 'scan_truncated':len(raw)>131072,
            'raw_text_retained':False}

def read_private(path, limit):
    need(path.resolve()==path, 'source_symlink_rejected')
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        s = os.fstat(f.fileno())
        need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o077, 'private_source_permissions_required')
        data=f.read(limit+1)
    need(len(data)<=limit, 'source_size_limit')
    return data

def inspect_existing():
    result={'scope':'fixed documented paths only; no repository requests', 'logs':[], 'artifacts':[],
            'actionable_restore_error_recovered':False}
    verified=[]
    for path in LOGS:
        row={'path':str(path), 'exists':path.exists()}
        if path.exists():
            try:
                raw=read_private(path,131072);row['sanitized']=sanitize(raw)
                if b'pg_restore: error:' in raw and (row['sanitized']['sqlstates'] or
                    row['sanitized']['categories']!=['unclassified_postgresql_error']):
                    result['actionable_restore_error_recovered']=True
            except (Stop,OSError): row['status']='unreadable_or_not_private_bounded_log'
        result['logs'].append(row)
    for path in PATHS:
        row={'path':str(path), 'exists':path.exists()}
        if path.exists():
            try:
                data=read_private(path,DUMP_SIZE)
                row['verified']=len(data)==DUMP_SIZE and hashlib.sha256(data).hexdigest()==DUMP_SHA
                if row['verified']: verified.append(path)
            except (Stop,OSError): row['verified']=False
        result['artifacts'].append(row)
    return result, verified

def docker(*args, data=None, timeout=30, check=True):
    # The caller can neither select a remote endpoint nor import/pull an image.
    need(args and args[0] in {'image','ps','inspect','create','start','exec','rm'}, 'unapproved_docker_operation')
    if args[0]=='image': need(args[1]=='inspect','image_mutation_forbidden')
    p=subprocess.run(['/usr/bin/docker','--host','unix:///var/run/docker.sock',*args],
                     input=data,capture_output=True,timeout=timeout,env=ENV)
    if check and p.returncode: raise Stop('docker_operation_failed')
    return p

def inventory():
    ids=docker('ps','-aq').stdout.decode().split()
    need(len(ids)<100,'inventory_limit')
    rows=json.loads(docker('inspect',*ids).stdout) if ids else []
    return sorted((r['Id'],r['Image'],r['State']['Running'],r['RestartCount'],
        hashlib.sha256(json.dumps([r['Config'],r['HostConfig']],sort_keys=True).encode()).hexdigest()) for r in rows)

def persist(result, first=False):
    flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_EXCL if first else os.O_TRUNC)
    with os.fdopen(os.open(RECEIPT,flags,0o600),'w') as f:
        os.fchmod(f.fileno(),0o600);json.dump(result,f,indent=2);f.flush();os.fsync(f.fileno())

def restore_once(path, inspection):
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'single_use_receipt_exists_do_not_repeat')
    # This uses the existing daemon only for a new owned diagnostic container.
    # No production container, volume, network, image or configuration is changed.
    need(json.loads(docker('image','inspect',IMAGE).stdout)[0]['Id']==IMAGE,'cached_postgresql_image_missing_or_changed')
    need(shutil.disk_usage(ROOT).free>=1000000000,'disk_reserve_required')
    mem=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    need(mem>=1500000000,'memory_reserve_required')
    dump=read_private(path,DUMP_SIZE)
    need(len(dump)==DUMP_SIZE and hashlib.sha256(dump).hexdigest()==DUMP_SHA,'dump_changed')
    baseline=inventory();run=uuid.uuid4().hex;cid=None
    result={'operation':'approved-restore-only-diagnostic-20261104-1','status':'running',
            'inspection':inspection,'b2_requests':0,'image_imports':0,'application_started':False,
            'restore_attempts':0,'stage':'create_owned_database','run_id':run}
    persist(result,first=True)
    try:
        cid=docker('create','--pull','never','--name','abap-restore-only-'+run,
            '--label','com.abap.restore-only='+run,'--network','none','--read-only',
            '--memory','768m','--cpus','0.75','--pids-limit','160','--restart','no','--log-driver','none',
            '--cap-drop','ALL','--cap-add','CHOWN','--cap-add','DAC_OVERRIDE','--cap-add','FOWNER',
            '--cap-add','SETGID','--cap-add','SETUID','--security-opt','no-new-privileges',
            '--tmpfs','/var/lib/postgresql:rw,nosuid,nodev,size=256m',
            '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16m',
            '-e','POSTGRES_DB=abap_recovered','-e','POSTGRES_USER=rehearsal_admin',
            '-e','POSTGRES_PASSWORD='+uuid.uuid4().hex,IMAGE,'postgres','-c','listen_addresses=127.0.0.1',
            '-c','shared_buffers=64MB','-c','max_connections=20','-c','autovacuum=off',
            '-c','shared_preload_libraries=','-c','logging_collector=on','-c','log_directory=/tmp',
            '-c','log_filename=abap-pg-diagnostic.log','-c','log_file_mode=0600',
            '-c','log_error_verbosity=verbose','-c','log_statement=none',
            '-c','log_min_error_statement=panic').stdout.decode().strip()
        need(re.fullmatch('[0-9a-f]{64}',cid),'invalid_owned_container_id')
        info=json.loads(docker('inspect',cid).stdout)[0];host=info['HostConfig']
        need(info['Image']==IMAGE and info['Config']['Labels'].get('com.abap.restore-only')==run
             and host['NetworkMode']=='none' and host['ReadonlyRootfs'] and not host.get('Privileged')
             and not host.get('Binds') and not host.get('PortBindings')
             and all(m['Type']=='tmpfs' for m in info['Mounts']), 'isolation_verification_failed')
        result['stage']='wait_owned_database';persist(result);docker('start',cid)
        deadline=time.monotonic()+90
        while docker('exec',cid,'pg_isready','-U','rehearsal_admin','-d','abap_recovered',check=False).returncode:
            need(time.monotonic()<deadline,'database_readiness_timeout');time.sleep(.5)
        result['stage']='restore_postgresql_archive';result['restore_attempts']=1;persist(result)
        p=docker('exec','-i',cid,'pg_restore','--exit-on-error','--single-transaction','--no-owner',
                 '--no-privileges','-U','rehearsal_admin','--dbname','abap_recovered',data=dump,timeout=180,check=False)
        result['restore_exit_code']=p.returncode;result['postgresql_error']=sanitize(p.stderr)
        result['status']='PASS-isolated-restore-only' if p.returncode==0 else 'FAIL-isolated-restore-only'
    except subprocess.TimeoutExpired: result.update(status='BLOCKED-timeout',error='bounded_operation_timeout')
    except (Stop,OSError,ValueError) as e: result.update(status='BLOCKED-diagnostic',error=str(e) if isinstance(e,Stop) else 'operation_error_suppressed')
    finally:
        # Finish bounded cleanup if the operator disconnects or terminates the run.
        for name in ['SIGINT','SIGTERM','SIGHUP']:
            if hasattr(signal,name): signal.signal(getattr(signal,name),signal.SIG_IGN)
        if not cid:
            try:
                ids=docker('ps','-aq','--filter','label=com.abap.restore-only='+run).stdout.decode().split()
                need(len(ids)<=1,'ambiguous_owned_container_after_create')
                if ids: cid=ids[0]
            except (Stop,OSError,ValueError,subprocess.TimeoutExpired):
                result['cleanup']='BLOCKED-owned-resource-identity-unavailable'
        if cid:
            try:
                info=json.loads(docker('inspect',cid).stdout)[0]
                need(info['Id']==cid and info['Config']['Labels'].get('com.abap.restore-only')==run,'cleanup_identity_changed')
                log=docker('exec','-u','postgres',cid,'head','-c','131072','/tmp/abap-pg-diagnostic.log',check=False)
                result['postgresql_server_error']=sanitize(log.stdout) if log.returncode==0 else {'status':'unavailable'}
                docker('rm','-f',cid);result['cleanup']='PASS'
            except (Stop,OSError,ValueError,subprocess.TimeoutExpired): result['cleanup']='BLOCKED-owned-resource-preserved'
        elif 'cleanup' not in result: result['cleanup']='PASS-no-container-created'
        try: result['production_state_preservation']='PASS' if inventory()==baseline else 'FAIL'
        except (Stop,OSError,ValueError,subprocess.TimeoutExpired): result['production_state_preservation']='BLOCKED'
        if result['cleanup'].startswith('BLOCKED') or result['production_state_preservation']!='PASS': result['status']='BLOCKED-cleanup-or-production-comparison'
        persist(result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect-existing',action='store_true')
    parser.add_argument('--approved-restore-if-local',action='store_true')
    args=parser.parse_args()
    need(os.geteuid()==0,'authenticated_sudo_required');os.umask(0o077)
    need(args.inspect_existing != args.approved_restore_if_local,'choose_one_explicit_mode')
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'private_receipt_parent_required')
    inspection,verified=inspect_existing()
    if args.inspect_existing: return {'status':'PASS-readonly-inspection','inspection':inspection,'restore_attempts':0}
    if inspection['actionable_restore_error_recovered']:
        return {'status':'PASS-existing-restore-error-recovered','inspection':inspection,'restore_attempts':0}
    if not verified: return {'status':'BLOCKED-verified-local-dump-unavailable','inspection':inspection,'restore_attempts':0,'b2_requests':0}
    return restore_once(verified[0],inspection)

if __name__=='__main__':
    def interrupted(signum,frame): raise Stop('operator_interrupted')
    for name in ['SIGTERM','SIGHUP']:
        if hasattr(signal,name): signal.signal(getattr(signal,name),interrupted)
    try: answer=main()
    except (Stop,OSError,ValueError,subprocess.TimeoutExpired) as e:
        answer={'status':'BLOCKED-before-diagnostic','code':str(e) if isinstance(e,Stop) else 'prerequisite_unavailable'}
    print(json.dumps(answer,indent=2))
    raise SystemExit(0 if answer['status'].startswith('PASS-') else 1)
