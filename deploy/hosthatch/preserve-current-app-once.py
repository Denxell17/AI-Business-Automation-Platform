#!/usr/bin/env python3
"""One approved image/config preservation. No service changes, DB writes or restores.

Sensitive configuration stays in memory and encrypted Restic streams. Output is safe
status/counts only. Restic's stdin command receives only the pinned Docker save command.
"""
import datetime
import ctypes
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import threading
import time
import zlib

IMAGE='sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9'
DB_IMAGE='sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280'
COMPOSE=Path('/opt/abap-public-rag-production/releases/0ef5085524b6-r2/compose.deploy.yaml')
ENV_FILE=Path('/etc/abap/production.env')
FILES=[COMPOSE,ENV_FILE,Path('/etc/caddy/Caddyfile'),
 Path('/etc/abap/credentials/public-rag-production/gateway-token'),
 Path('/etc/abap/credentials/public-rag-production/turnstile-secret')]
LIB=Path('/usr/local/lib/abap/abap-operations-lib.sh')
RESTIC=Path('/usr/local/bin/restic')
ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-current-application-preservation-20261103-1.json'
RUN='approved-current-application-preservation-20261103-1'
ENV={'PATH':'/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/nonexistent','LC_ALL':'C',
 'DOCKER_HOST':'unix:///var/run/docker.sock','GOMAXPROCS':'1','GOMEMLIMIT':'256MiB'}
DEADLINE=None
OWN=False
report={'operation':RUN,'preconditions':{},'snapshots':{},'production_services_modified':False,
 'database_modified_or_restored':False,'timers_changed':False,'snapshots_deleted':False,'n8n_drills_repeated':False}

class Blocked(Exception):pass
def require(value,code):
    if not value:raise Blocked(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def trusted(path,private=False):
    s=path.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&(0o077 if private else 0o022),'untrusted_operations_file')
def save():
    if OWN:
        with os.fdopen(os.open(RECEIPT,os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW),'w') as f:
            json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def bounded_worker(args,consumer=None,data=None,timeout=180,max_output=32_000_000,clean_env=None):
    """Bound streaming reads/writes and suppress all raw child errors, including secrets."""
    if DEADLINE is not None:timeout=min(timeout,DEADLINE-time.monotonic())
    require(timeout>0,'operation_deadline')
    p=subprocess.Popen(args,stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=clean_env or ENV,start_new_session=True)
    answer=[];errors=[]
    def work():
        try:
            if consumer is not None:answer.append(consumer(p.stdout));p.stdout.close();p.wait()
            else:
                out,_=p.communicate(data);require(len(out)<=max_output,'bounded_output_exceeded');answer.append(out)
            require(p.returncode==0,'child_failed_raw_output_suppressed')
        except BaseException as e:errors.append(e)
    thread=threading.Thread(target=work,daemon=True);thread.start();end=time.monotonic()+timeout
    try:
        while thread.is_alive():
            thread.join(min(20,max(.01,end-time.monotonic())))
            if not thread.is_alive():break
            require(time.monotonic()<end,'bounded_operation_timeout')
            print(json.dumps({'event':'preservation_running','step':report.get('step','preflight')}),flush=True)
        if errors:raise errors[0]
        return answer[0]
    finally:
        if p.poll() is None:
            os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
        thread.join(timeout=5)
        for stream in [p.stdin,p.stdout,p.stderr]:
            if stream and not stream.closed:stream.close()
def call(args,**kw):return bounded_worker(args,**kw)
def docker(*args,**kw):return call(['/usr/bin/docker',*args],**kw)
def operations(code,args=(),**kw):
    return call(['/bin/bash','--noprofile','--norc','-c',
        'set -Eeuo pipefail; source "$1"; shift; operations_load_config; operations_configure_restic; '+code,
        'approved-preservation',str(LIB),*args],**kw)
def restic(*args,**kw):
    require(args and args[0] in {'snapshots','ls','dump','stats','list','backup'},'repository_mutation_forbidden')
    if args[0]=='backup':
        require(OWN and ('--stdin' in args or '--stdin-from-command' in args) and '--json' in args,'unapproved_backup_mode')
        flags='--no-cache '
    else:flags='--no-lock --no-cache '
    return operations('executable="$1"; shift; exec "$executable" '+flags+'--limit-upload 2048 --limit-download 8192 "$@"',
        (str(RESTIC),*args),**kw)
def signature(path):
    s=path.lstat();return(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def source(path):
    require(path.resolve()==path,'configuration_symlink_requires_review')
    before=signature(path);require(stat.S_ISREG(before[2]) and before[5]<=8_000_000,'configuration_source_limit')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as f:data=f.read(8_000_001)
    require(signature(path)==before and len(data)==before[5],'configuration_changed_during_read')
    return data,before
def inventory():
    ids=docker('ps','-aq').decode().split();require(0<len(ids)<=100,'container_inventory_limit')
    rows=json.loads(docker('inspect',*ids));selected=[]
    for i in rows:
        if (i.get('Config',{}).get('Labels') or {}).get('com.docker.compose.project') in {'abap-deploy','n8n','abap-public-rag-production'}:
            selected.append((i['Id'],i['Image'],i.get('RestartCount'),i['State'].get('Status'),i['State'].get('StartedAt'),sha(json.dumps(i['Config'],sort_keys=True).encode())))
    return sorted(selected),rows
def service(rows,name):
    values=[r for r in rows if (r.get('Config',{}).get('Labels') or {}).get('com.docker.compose.project')=='abap-deploy'
        and (r.get('Config',{}).get('Labels') or {}).get('com.docker.compose.service')==name and r['State'].get('Running')]
    require(len(values)==1,'authoritative_service_ambiguous');return values[0]
def envmap(values):
    result={}
    for row in values or []:
        key,sep,value=row.partition('=');require(sep and key not in result,'invalid_or_duplicate_environment');result[key]=value
    return result
def reconcile(web,image,resolved):
    live=envmap(web['Config'].get('Env'));defaults=envmap(image['Config'].get('Env'))
    expected={**defaults,**{k:str(v) for k,v in resolved['services']['web'].get('environment',{}).items()}}
    require(live==expected,'runtime_environment_not_fully_reconciled')
    return {'status':'PASS','configured_keys':len(resolved['services']['web'].get('environment',{})),
        'image_default_extra_keys':len(set(live)-set(resolved['services']['web'].get('environment',{})))}
class HashedReader:
    def __init__(self,stream,limit):self.stream=stream;self.limit=limit;self.count=0;self.h=hashlib.sha256()
    def read(self,n=-1):
        require(n>=0,'unbounded_stream_read');data=self.stream.read(n);self.count+=len(data)
        require(self.count<=self.limit,'image_stream_capacity_limit');self.h.update(data);return data
class ZstdDecoder:
    """Bounded streaming libzstd dependency; no package installation or shell decoder."""
    class Buffer(ctypes.Structure):
        _fields_=[('pointer',ctypes.c_void_p),('size',ctypes.c_size_t),('position',ctypes.c_size_t)]
    def __init__(self):
        candidates=[Path('/lib/x86_64-linux-gnu/libzstd.so.1'),Path('/usr/lib/x86_64-linux-gnu/libzstd.so.1')]
        name=next((p.resolve() for p in candidates if p.is_file()),None)
        require(name is not None,'zstd_decoder_dependency_missing');trusted(name)
        self.lib=ctypes.CDLL(str(name));self.context=None
        self.lib.ZSTD_createDStream.restype=ctypes.c_void_p
        self.lib.ZSTD_freeDStream.argtypes=[ctypes.c_void_p];self.lib.ZSTD_freeDStream.restype=ctypes.c_size_t
        self.lib.ZSTD_initDStream.argtypes=[ctypes.c_void_p];self.lib.ZSTD_initDStream.restype=ctypes.c_size_t
        self.lib.ZSTD_DCtx_setMaxWindowSize.argtypes=[ctypes.c_void_p,ctypes.c_size_t];self.lib.ZSTD_DCtx_setMaxWindowSize.restype=ctypes.c_size_t
        self.lib.ZSTD_isError.argtypes=[ctypes.c_size_t];self.lib.ZSTD_isError.restype=ctypes.c_uint
        self.lib.ZSTD_decompressStream.argtypes=[ctypes.c_void_p,ctypes.POINTER(self.Buffer),ctypes.POINTER(self.Buffer)];self.lib.ZSTD_decompressStream.restype=ctypes.c_size_t
        self.context=self.lib.ZSTD_createDStream();require(self.context,'zstd_allocation_failed')
        self.check(self.lib.ZSTD_initDStream(self.context));self.check(self.lib.ZSTD_DCtx_setMaxWindowSize(self.context,64*1024*1024));self.remaining=1
    def check(self,result):require(not self.lib.ZSTD_isError(result),'zstd_image_blob_invalid')
    def parts(self,data):
        storage=ctypes.create_string_buffer(data);incoming=self.Buffer(ctypes.cast(storage,ctypes.c_void_p),len(data),0)
        while True:
            output=ctypes.create_string_buffer(1024*1024);outgoing=self.Buffer(ctypes.cast(output,ctypes.c_void_p),len(output),0)
            before=incoming.position;self.remaining=self.lib.ZSTD_decompressStream(self.context,ctypes.byref(outgoing),ctypes.byref(incoming));self.check(self.remaining)
            if outgoing.position:yield output.raw[:outgoing.position]
            if incoming.position==incoming.size and (outgoing.position<outgoing.size or self.remaining==0):break
            require(incoming.position>before or outgoing.position,'zstd_decoder_no_progress')
    @property
    def eof(self):return self.remaining==0
    def close(self):
        if self.context:self.lib.ZSTD_freeDStream(self.context);self.context=None
    def __del__(self):
        if getattr(self,'context',None):self.close()
def verify_image(stream):
    reader=HashedReader(stream,1_200_000_000);hashes={};plain_hashes={};documents={};man=None;count=0;metadata_bytes=0;expanded=0
    with tarfile.open(fileobj=reader,mode='r|') as tar:
        for member in tar:
            count+=1;require(count<=20000 and member.name not in hashes,'archive_member_limit_or_duplicate')
            require(not Path(member.name).is_absolute() and '..' not in Path(member.name).parts,'unsafe_image_archive_path')
            if member.isdir():continue
            require(member.isfile(),'image_archive_non_regular_member')
            file=tar.extractfile(member);h=hashlib.sha256();plain=hashlib.sha256()
            capture=member.size<=8_000_000 and (member.name.endswith('.json') or member.name.startswith('blobs/sha256/'))
            body=bytearray();decoder=None;first=True
            while True:
                data=file.read(1024*1024)
                if not data:break
                h.update(data)
                if first:
                    decoder=ZstdDecoder() if data.startswith(b'\x28\xb5\x2f\xfd') else zlib.decompressobj(16+zlib.MAX_WBITS) if data.startswith(b'\x1f\x8b') else None
                    first=False
                if isinstance(decoder,ZstdDecoder):
                    for part in decoder.parts(data):
                        plain.update(part);expanded+=len(part);require(expanded<=3_000_000_000,'expanded_image_capacity_limit')
                elif decoder:
                    pending=data
                    while pending:
                        part=decoder.decompress(pending,8_000_000);plain.update(part);expanded+=len(part)
                        require(expanded<=3_000_000_000,'expanded_image_capacity_limit');pending=decoder.unconsumed_tail
                else:plain.update(data);expanded+=len(data);require(expanded<=3_000_000_000,'expanded_image_capacity_limit')
                if capture:body.extend(data);require(len(body)<=8_000_000,'image_metadata_limit')
            digest=h.hexdigest();hashes[member.name]=digest
            if decoder:require(decoder.eof,'truncated_compressed_image_blob')
            if isinstance(decoder,ZstdDecoder):decoder.close()
            plain_hashes[member.name]=plain.hexdigest()
            if member.name.startswith('blobs/sha256/'):require(member.name.rsplit('/',1)[1]==digest,'oci_blob_digest_mismatch')
            if member.name=='manifest.json':man=json.loads(body)
            elif capture:
                try:document=json.loads(body)
                except (ValueError,UnicodeError):document=None
                if isinstance(document,dict) and ('rootfs' in document or 'schemaVersion' in document):
                    metadata_bytes+=len(body);require(metadata_bytes<=32_000_000,'image_document_capacity_limit')
                    documents['sha256:'+digest]=document
    while reader.read(1024*1024):pass
    require(isinstance(man,list) and len(man)==1,'unsupported_or_multi_image_export')
    row=man[0];config_digest='sha256:'+hashes.get(row.get('Config',''),'');config=documents.get(config_digest)
    require(config is not None,'image_configuration_missing')
    # Modern Docker's immutable ID may identify an OCI index/manifest, not config.
    # Prove the descriptor chain to the selected platform's exact config and layers.
    layer_digests=['sha256:'+hashes.get(p,'') for p in row.get('Layers',[])]
    visited=set()
    def reaches_config(digest):
        require(len(visited)<100,'image_descriptor_graph_limit')
        if digest in visited:return False
        visited.add(digest);node=documents.get(digest,{})
        if node.get('config',{}).get('digest')==config_digest:
            return [r.get('digest') for r in node.get('layers',[])]==layer_digests
        return any(reaches_config(r.get('digest')) for r in node.get('manifests',[]) if r.get('digest') in documents)
    require(config_digest==IMAGE or reaches_config(IMAGE),'image_manifest_identity_mismatch')
    layers=row.get('Layers',[]);diffs=config.get('rootfs',{}).get('diff_ids',[])
    require(len(layers)==len(diffs) and all('sha256:'+plain_hashes.get(p,'')==d for p,d in zip(layers,diffs)),'image_layer_integrity_mismatch')
    require(config.get('os')=='linux' and config.get('architecture')=='amd64','image_platform_mismatch')
    return {'status':'PASS','image_id':IMAGE,'configuration_digest':config_digest,'archive_sha256':reader.h.hexdigest(),'archive_bytes':reader.count,
        'layers_verified':len(layers),'image_load_test':'NOT-PERFORMED'}
def tar_package(files,metadata):
    manifest={'format':'abap-current-config-v1','image_id':IMAGE,'files':{}}
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w') as tar:
        for name,(data,sig) in files.items():
            require(not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe_package_path')
            uid,gid,mode=(sig[3],sig[4],stat.S_IMODE(sig[2])) if sig else (0,0,0o600)
            item=tarfile.TarInfo(name);item.size=len(data);item.uid=uid;item.gid=gid;item.mode=mode;tar.addfile(item,io.BytesIO(data))
            manifest['files'][name]={'sha256':sha(data),'bytes':len(data),'uid':uid,'gid':gid,'mode':mode}
        manifest['metadata']=metadata
        body=json.dumps(manifest,sort_keys=True).encode();item=tarfile.TarInfo('manifest.json');item.size=len(body);item.mode=0o600;tar.addfile(item,io.BytesIO(body))
    payload=out.getvalue();require(len(payload)<=32_000_000,'configuration_package_limit');return payload
def verify_package(payload,expected):
    require(sha(payload)==sha(expected),'configuration_readback_checksum_mismatch')
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:') as tar:
        members=tar.getmembers();require(len({m.name for m in members})==len(members),'configuration_duplicate_member')
        manifest=json.load(tar.extractfile('manifest.json'));require(manifest['image_id']==IMAGE,'configuration_image_identity_mismatch')
        require({m.name for m in members}==set(manifest['files'])|{'manifest.json'},'configuration_coverage_mismatch')
        for name,entry in manifest['files'].items():
            require(not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe_configuration_member')
            member=tar.getmember(name);require(member.isfile(),'configuration_non_regular_member')
            data=tar.extractfile(member).read();require(sha(data)==entry['sha256'] and len(data)==entry['bytes'],'configuration_file_checksum_mismatch')
            require((member.uid,member.gid,member.mode)==(entry['uid'],entry['gid'],entry['mode']),'configuration_file_metadata_mismatch')
    return {'status':'PASS','archive_sha256':sha(payload),'archive_bytes':len(payload),'verified_files':len(manifest['files'])}
def database_backup(catalog,host,db):
    expected={'/var/backups/abap/staging','/var/lib/docker/volumes/abap-deploy_invoice_documents/_data'}
    rows=[r for r in catalog if {p.rstrip('/') for p in r.get('paths',[])}==expected and r.get('hostname')==host and 'abap-production' in r.get('tags',[])]
    require(rows,'authoritative_database_backup_not_identified');row=max(rows,key=lambda x:x['time'])
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(row['time'].replace('Z','+00:00'))).total_seconds()
    require(0<=age<=86400,'database_backup_outside_24h_precondition')
    prefix='/var/backups/abap/staging/';sid=row['id']
    manifest=restic('dump',sid,prefix+'RECOVERY-MANIFEST.txt',max_output=128000)
    values=dict(line.split('=',1) for line in manifest.decode().splitlines() if '=' in line)
    require(values.get('format')=='abap-production-backup-v1' and values.get('compose_project')=='abap-deploy'
        and values.get('database_image')==db['Config']['Image'] and values.get('postgresql_dump')=='database.dump'
        and values.get('invoice_documents_source')=='/var/lib/docker/volumes/abap-deploy_invoice_documents/_data','database_backup_provenance_mismatch')
    checks=restic('dump',sid,prefix+'SHA256SUMS',max_output=1_000_000).decode().splitlines()
    expected_hash={}
    for line in checks:
        parts=line.split(maxsplit=1)
        if len(parts)==2 and re.fullmatch('[0-9a-f]{64}',parts[0]):expected_hash[parts[1].lstrip('*')]=parts[0]
    require(expected_hash.get('RECOVERY-MANIFEST.txt')==sha(manifest),'database_backup_manifest_checksum_mismatch')
    size=int(values.get('postgresql_dump_bytes','0'));require(0<size<=64_000_000,'database_dump_size_requires_separate_review')
    dump=restic('dump',sid,prefix+'database.dump',max_output=64_000_000)
    require(len(dump)==size and expected_hash.get('database.dump')==sha(dump) and dump.startswith(b'PGDMP'),'database_dump_authentication_failed')
    current=docker('exec',db['Id'],'postgres','--version').decode()
    major=lambda v:re.search(r'PostgreSQL\)?\s+(\d+)',v)
    require(major(current) and major(values.get('postgres_version','')) and major(current)[1]==major(values['postgres_version'])[1],'database_major_version_mismatch')
    # Neither command uses --dbname: both parse the archive without a DB connection.
    toc=docker('exec','-i',db['Id'],'pg_restore','--list',data=dump,timeout=120,max_output=4_000_000).decode()
    names=re.findall(r'(?m)^;\s+dbname:\s*([^\r\n]+)',toc)
    live_env=envmap(db['Config'].get('Env'));expected_name=live_env.get('POSTGRES_DB') or live_env.get('POSTGRES_USER') or 'postgres'
    require(len(names)==1 and names[0].strip()==expected_name,'archive_database_name_mismatch')
    docker('exec','-i',db['Id'],'pg_restore','--file=/dev/null',data=dump,timeout=120,max_output=128000)
    return {'status':'PASS-archive-authentication-and-full-offline-parse','snapshot_id':sid,'snapshot_time':row['time'],
        'dump_bytes':size,'dump_sha256':sha(dump),'postgresql_major':major(current)[1],'project_and_source_provenance':'PASS','archive_database_identity':'PASS',
        'full_database_restore_test':'NOT-PERFORMED','business_data_printed':False}
def snapshot_id(raw):
    rows=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    summaries=[r for r in rows if r.get('message_type')=='summary']
    require(len(summaries)==1 and re.fullmatch('[0-9a-f]{64}',summaries[0].get('snapshot_id','')),'new_snapshot_id_missing')
    return summaries[0]['snapshot_id']
def main():
    global DEADLINE,OWN
    require(len(sys.argv)==1 and os.geteuid()==0,'authenticated_sudo_no_arguments_required')
    DEADLINE=time.monotonic()+2400;os.umask(0o077);os.nice(15)
    require(ROOT.resolve()==ROOT and ROOT.is_dir() and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'unsafe_receipt_parent')
    require(not RECEIPT.exists() and not RECEIPT.is_symlink(),'single_use_operation_already_reserved')
    for p,private in [(LIB,False),(RESTIC,False),(Path('/etc/abap/operations.conf'),True)]:trusted(p,private)
    lock=os.open('/run/lock/abap-production-backup.lock',os.O_RDWR|os.O_NOFOLLOW)
    try:
        lock_stat=os.fstat(lock)
        require(stat.S_ISREG(lock_stat.st_mode) and lock_stat.st_uid==0 and not lock_stat.st_mode&0o077,'untrusted_existing_backup_lock')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before,rows=inventory();web=service(rows,'web');db=service(rows,'database')
        require(web['Image']==IMAGE and db['Image']==DB_IMAGE,'running_image_changed')
        image=json.loads(docker('image','inspect',IMAGE))[0];require(image['Id']==IMAGE,'immutable_image_missing')
        labels=web['Config'].get('Labels') or {}
        require(labels.get('com.docker.compose.project.config_files')==str(COMPOSE)
            and labels.get('com.docker.compose.project.working_dir')==str(COMPOSE.parent)
            and labels.get('com.docker.compose.project.environment_file')==str(ENV_FILE),'current_compose_sources_changed')
        compose_args=['compose','--project-directory',str(COMPOSE.parent),'--env-file',str(ENV_FILE),'-p','abap-deploy','-f',str(COMPOSE)]
        resolved=json.loads(docker(*compose_args,'config','--format','json'))
        view=resolved['services']['web']
        require(view.get('image')==web['Config']['Image'] and view.get('command')==web['Config'].get('Cmd')
            and view.get('entrypoint',image['Config'].get('Entrypoint'))==web['Config'].get('Entrypoint'),'current_compose_runtime_mismatch')
        report['preconditions']['runtime_environment']=reconcile(web,image,resolved)
        settings=operations('printf "%s\\n" "$ABAP_RESTIC_HOST" "$ABAP_RESTIC_CRITICAL_BYTES" "$ABAP_RESTIC_PREFLIGHT_OVERHEAD_BYTES"').decode().splitlines()
        require(len(settings)==3,'repository_capacity_settings_missing');host=settings[0];critical,overhead=map(int,settings[1:])
        catalog=json.loads(restic('snapshots','--json'));original={r['id'] for r in catalog}
        require(not any(RUN in r.get('tags',[]) for r in catalog),'operation_snapshot_already_exists_do_not_repeat')
        require(not restic('list','locks').strip(),'repository_locked_no_unlock_authorized')
        report['step']='verify-existing-database-backup'
        report['preconditions']['database_backup']=database_backup(catalog,host,db)
        # Entire package is assembled in memory BEFORE any receipt/snapshot creation.
        sources={};signatures={}
        for p in FILES:
            data,sig=source(p);sources['files'+str(p)]=(data,sig);signatures[p]=sig
        # Unknown includes or proxy secret dependencies must not be silently omitted.
        proxy=sources['files/etc/caddy/Caddyfile'][0].decode()
        require(not re.search(r'(?m)^\s*import\s|\{\$[A-Za-z_]|(?m:^\s*tls\s+/)',proxy),'proxy_additional_dependency_requires_review')
        raw_compose=sources['files'+str(COMPOSE)][0].decode()
        require(not re.search(r'(?m)^\s*(?:include|extends)\s*:',raw_compose),'compose_include_dependency_requires_review')
        unresolved=json.loads(docker(*compose_args,'config','--no-env-resolution','--format','json'))
        require(not unresolved['services']['web'].get('env_file') and not view.get('configs'),'additional_configuration_file_requires_review')
        secret_sources=set()
        for ref in view.get('secrets',[]):
            name=ref.get('source') if isinstance(ref,dict) else ref
            definition=resolved.get('secrets',{}).get(name,{})
            require(definition.get('file'),'external_secret_requires_review');secret_sources.add(Path(definition['file']))
        require(secret_sources==set(FILES[3:]),'secret_dependency_set_changed')
        actual_binds={Path(m['Source']) for m in web.get('Mounts',[]) if m.get('Type')=='bind'}
        require(actual_binds==set(FILES[3:]) and all(not m.get('RW') for m in web.get('Mounts',[]) if m.get('Type')=='bind'),'bind_dependency_set_changed')
        volumes={m['Name'] for m in web.get('Mounts',[]) if m.get('Type')=='volume'}
        require(volumes=={'abap-deploy_activity_logs','abap-deploy_invoice_documents'},'persistent_volume_dependency_changed')
        volume_meta=json.loads(docker('volume','inspect',*sorted(volumes)))
        require(all((v.get('Labels') or {}).get('com.docker.compose.project')=='abap-deploy' for v in volume_meta),'volume_project_mismatch')
        names=sorted(web.get('NetworkSettings',{}).get('Networks',{}))
        require(set(names)=={'abap-deploy_default','abap_public_rag_private'},'network_dependency_set_changed')
        networks=json.loads(docker('network','inspect',*names))
        require(any(n['Name']=='abap_public_rag_private' and n.get('Internal') is True for n in networks),'private_network_configuration_changed')
        sources['private/runtime.json']=(json.dumps({'web':web,'database_identity':{'id':db['Id'],'image':db['Image']},'image':image,'volumes':volume_meta,'networks':networks}).encode(),None)
        sources['private/compose-resolved.json']=(json.dumps(resolved).encode(),None)
        provenance=COMPOSE.parent/'deploy/production/audit-public-rag-production-preflight.sh'
        if provenance.is_file():
            data,sig=source(provenance);sources['files'+str(provenance)]=(data,sig);signatures[provenance]=sig
        payload=tar_package(sources,{'database_backup':report['preconditions']['database_backup'],'migration_strategy':'retain additive 014-016 on web rollback; ledger 001-013 from prior approved evidence; no migrations here',
            'docker_version':docker('version','--format','{{.Server.Version}}').decode().strip(),'compose_version':docker('compose','version','--short').decode().strip()})
        verify_package(payload,payload)
        report['step']='preflight-image-export-validation'
        reusable=[r for r in catalog if 'artifact-image' in r.get('tags',[]) and 'image-id-'+IMAGE[7:] in r.get('tags',[])]
        reused=max(reusable,key=lambda r:r['time']) if reusable else None
        if reused:
            export=restic('dump',reused['id'],'/application-image.tar',consumer=verify_image,timeout=900)
            report['snapshots']['image']={'id':reused['id'],'timestamp':reused['time'],'verification':export,'reused':True}
        else:export=bounded_worker(['/usr/bin/docker','image','save',IMAGE],consumer=verify_image,timeout=240)
        raw=int(json.loads(restic('stats','--mode','raw-data','--json'))['total_size'])
        free=shutil.disk_usage(ROOT).free
        memory=next((int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')),0)
        require(memory>=1_000_000_000,'memory_headroom_precondition_failed')
        require(free>=3_500_000_000 and raw+(0 if reused else export['archive_bytes'])+len(payload)+overhead<critical,'capacity_precondition_failed')
        require(inventory()[0]==before and all(signature(p)==s for p,s in signatures.items())
            and json.loads(docker(*compose_args,'config','--format','json'))==resolved,'production_changed_before_reservation')
        report['preconditions'].update(image={'status':'PASS','id':IMAGE,'tag':web['Config']['Image'],'archive_preflight':export},
            capacity={'status':'PASS','free_bytes':free,'memory_available_bytes':memory,'repository_raw_bytes':raw,'critical_bytes':critical},configuration={'status':'PASS','source_files':len(signatures),'plaintext_staged':False})
        # All prerequisites passed. Only now reserve the single authorized operation.
        fd=os.open(RECEIPT,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(fd);OWN=True
        report['started_at']=utc();report['controller_sha256']=sha(Path(__file__).read_bytes());report['status']='reserved';save()
        for kind,filename in [('image','application-image.tar'),('configuration','application-configuration.tar')]:
            if kind=='image' and reused:continue
            report['step']='upload-'+kind;save()
            args=['backup','--json','--host',host,'--tag','abap-production','--tag','release','--tag',RUN,'--tag','artifact-'+kind,'--stdin-filename',filename]
            if kind=='image':
                args+=['--tag','image-id-'+IMAGE[7:]]
                raw_result=restic(*args,'--stdin-from-command','--','/usr/bin/docker','image','save',IMAGE,timeout=900)
            else:raw_result=restic(*args,'--stdin',data=payload,timeout=300)
            sid=snapshot_id(raw_result);report['snapshots'][kind]={'id':sid,'verification':'pending'};save()
            updated=json.loads(restic('snapshots','--json'));matches=[r for r in updated if r['id']==sid]
            require(len(matches)==1 and RUN in matches[0].get('tags',[]) and 'release' in matches[0].get('tags',[])
                and matches[0].get('hostname')==host
                and ['/'+p.lstrip('/') for p in matches[0].get('paths',[])]==['/'+filename]
                and datetime.datetime.fromisoformat(matches[0]['time'].replace('Z','+00:00'))>=datetime.datetime.fromisoformat(report['started_at']),
                'snapshot_scope_verification_failed')
            report['snapshots'][kind]['timestamp']=matches[0]['time'];save()
            report['step']='readback-'+kind;save()
            # Restic stdin paths are absolute root-level artifact names, not live paths.
            if kind=='image':check=restic('dump',sid,'/'+filename,consumer=verify_image,timeout=900)
            else:check=verify_package(restic('dump',sid,'/'+filename,max_output=32_000_000),payload)
            report['snapshots'][kind]['verification']=check;save()
        final=json.loads(restic('snapshots','--json'));require(original<={r['id'] for r in final},'prior_snapshot_missing')
        new=[r for r in final if RUN in r.get('tags',[])]
        expected_new={r['id'] for r in report['snapshots'].values() if not r.get('reused')}
        require(len(new)==len(expected_new) and len(new)<=2 and {r['id'] for r in new}==expected_new,'authorized_snapshot_budget_exceeded')
        require(inventory()[0]==before and all(signature(p)==s for p,s in signatures.items())
            and json.loads(docker(*compose_args,'config','--format','json'))==resolved,'production_changed_during_preservation')
        report.update(status='PASS-encrypted-current-application-preservation',completed_at=utc(),previous_snapshots_preserved=True,production_state_unchanged=True,
            limits=['No image load, application boot or actual database restore test performed','Full host disaster recovery, TLS reissuance and external provider availability remain separate dependencies','No service changes, migration, timer activation or assistant deployment authorized'])
        save()
    finally:os.close(lock)
if __name__=='__main__':
    def interrupted(signum,frame):raise Blocked('operation_interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    try:main()
    except BaseException as error:
        report['status']='BLOCKED-no-snapshots-created' if not OWN else 'FAIL-or-BLOCKED-partial-operation-do-not-repeat'
        report['failure_code']=str(error) if isinstance(error,Blocked) else 'raw_error_suppressed'
        if OWN:save()
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report.get('status')=='PASS-encrypted-current-application-preservation' else 1)
