"""Isolated recovery engine. Caller supplies a private Docker endpoint, never Compose.

No production credentials are passed to containers. All raw outputs remain private.
"""
import json
import secrets
import re
import subprocess
import time
from urllib.parse import quote

class Blocked(Exception):pass
class CommandFailure(Blocked):
    def __init__(self,diagnostic):
        super().__init__('isolated_command_'+diagnostic['classification']);self.diagnostic=diagnostic

ERROR_PATTERNS=[
 ('permission','permission_denied','permission denied'),('permission','operation_not_permitted','operation not permitted'),
 ('permission','readonly_filesystem','read-only file system'),('resource','disk_full','no space left on device'),
 ('resource','memory_exhausted','out of memory'),('resource','allocation_failed','cannot allocate memory'),
 ('resource','resource_unavailable','resource temporarily unavailable'),('daemon','daemon_unreachable','cannot connect to the docker daemon'),
 ('daemon','connection_refused','connection refused'),('runtime','cgroup_error','cgroup'),
 ('runtime','container_runtime_create_failed','runc create failed'),('namespace','namespace_create_failed','failed to create namespace'),
 ('image_import','invalid_tar_header','invalid tar header'),('image_import','unsupported_media_type','unsupported media type'),
 ('image_import','unrecognized_image_format','unrecognized image format'),('image_import','layer_extraction_failed','failed to extract layer'),
 ('image_import','image_not_found','no such image'),('postgresql','pg_restore_error','pg_restore: error'),
 ('postgresql','psql_error','psql: error'),('postgresql','initdb_error','initdb: error'),
 ('postgresql','database_version_incompatible','database files are incompatible'),
 ('runtime','shared_library_missing','error while loading shared libraries'),
 ('runtime','logging_configuration_invalid','failed to initialize logging driver')]
def safe_id(value):
    return value if isinstance(value,str) and re.fullmatch(r'[a-z0-9_]{1,64}',value) else 'unclassified_operation'
def command_identifier(args):
    first=str(args[0]) if args else ''
    if first=='exec':
        for binary in ['pg_restore','pg_isready','psql','postgres','python']:
            if binary in args:return 'docker_exec_'+binary
    if first in {'version','load','create','start','inspect','rm','ps'}:return 'docker_'+first
    if first in {'image','network','volume'} and len(args)>1 and args[1]=='inspect':return 'docker_'+first+'_inspect'
    return 'docker_operation'
def diagnostic(stage,command_id,exit_code=None,stderr=b'',timeout=None,classification='exit_failure'):
    raw=stderr if isinstance(stderr,bytes) else str(stderr).encode();text=raw[:65536].decode('utf-8','replace').casefold()
    matches=[(category,code) for category,code,pattern in ERROR_PATTERNS if pattern in text][:8]
    domain='container_runtime_start' if command_id=='docker_start' else 'postgresql_readiness' if command_id=='docker_exec_pg_isready' else 'operation'
    components=[code for code,marker in [('containerd_shim','shim'),('containerd','containerd'),('runc','runc'),('ttrpc','ttrpc'),
        ('unix_socket','dial unix'),('filesystem_unix_socket','dial unix /'),('abstract_unix_socket','dial unix @')] if marker in text]
    return {'stage':safe_id(stage),'command_id':safe_id(command_id),'classification':'timeout' if timeout is not None else classification,
        'failure_domain':domain,'runtime_components':components,
        'exit_code':exit_code,'timeout_seconds':timeout,'stderr_category':matches[0][0] if matches else 'none' if not raw else 'unclassified',
        'details':[code for _,code in matches],'stderr_bytes':len(raw),'stderr_scan_truncated':len(raw)>65536,
        'raw_arguments_retained':False,'raw_stderr_retained':False}
def failure(error,stage,last=None):
    if isinstance(error,CommandFailure):return error.diagnostic
    result=diagnostic(stage,'verification',classification='guard_failure' if isinstance(error,Blocked) else 'internal_error')
    if isinstance(error,Blocked):result['code']=safe_id(getattr(error,'safe_code','unclassified_guard_failure'))
    if last and last.get('stage')==stage:result['last_command_failure']=last
    return result
BASE_ENV_KEYS={'PATH','LANG','LC_ALL','TZ','HOME','PYTHONDONTWRITEBYTECODE','PYTHONUNBUFFERED','PYTHON_VERSION','PYTHON_SHA256','GPG_KEY'}
def require(value,code):
    if not value:
        error=Blocked(code);error.safe_code=code;raise error

def daemon_configuration(root,run):
    return {'hosts':['unix://'+str(root/'docker.sock')],'data-root':str(root/'data'),
        'exec-root':str(root/'exec'),'pidfile':str(root/'dockerd.pid'),'storage-driver':'vfs',
        'bridge':'none','iptables':False,'ip6tables':False,'ip-forward':False,'ip-masq':False,
        'userland-proxy':False,'live-restore':False,'log-level':'error',
        'features':{'containerd-snapshotter':False},'exec-opts':['native.cgroupdriver=cgroupfs'],
        'cgroup-parent':'/abap-rehearsal-'+run,'group':'root'}

def safe_environment(original,password):
    # Allowlist rather than inheriting provider keys, endpoints or SMTP settings.
    safe={k:v for k,v in original.items() if k in BASE_ENV_KEYS}
    safe.update(DATABASE_BACKEND='postgresql',DATABASE_URL='postgresql://rehearsal_reader:'+quote(password,safe='')+'@127.0.0.1:5432/abap_recovered',
        ABAP_SESSION_SECRET=secrets.token_urlsafe(48),ABAP_INTEGRATIONS_ENABLED='false',ABAP_WORKER_ENABLED='false',
        ABAP_PUBLIC_RAG_ENABLED='false',ABAP_PUBLIC_RAG_LOGIN_UI_ENABLED='false',ABAP_ADVANCED_ASSISTANT_ENABLED='false',
        ABAP_ASSISTANT_REMOTE_APPROVED='false',ABAP_ASSISTANT_DEMO_ONLY='true',ABAP_ASSISTANT_N8N_WORKFLOW_ALLOWLIST='',
        PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
    return safe

class Docker:
    def __init__(self,prefix,run,checkpoint=None):
        self.prefix=prefix;self.run=run;self.owned={};self.checkpoint=checkpoint;self.stage='initialization';self.last_failure=None
        self.result={'status':'running','completed_stages':[],'command_events':[],'cleanup_attempts':[]}
    def persist(self):
        if self.checkpoint:self.checkpoint(self.result)
    def begin(self,stage):
        require(safe_id(stage)==stage,'invalid_diagnostic_stage');self.stage=stage;self.last_failure=None
        self.result['current_stage']=stage;self.persist()
    def complete(self):
        if self.stage not in self.result['completed_stages']:self.result['completed_stages'].append(self.stage)
        if self.result.get('last_command_failure',{}).get('stage')==self.stage:self.result.pop('last_command_failure',None)
        self.last_failure=None;self.persist()
    def call(self,*args,data=None,timeout=90):
        identity=command_identifier(args)
        try:p=subprocess.run([*self.prefix,*args],input=data,capture_output=True,timeout=timeout)
        except subprocess.TimeoutExpired as error:
            info=diagnostic(self.stage,identity,stderr=error.stderr or b'',timeout=timeout)
            self.last_failure=info;self.result['last_command_failure']=info;self.persist();raise CommandFailure(info) from None
        except OSError:
            info=diagnostic(self.stage,identity,classification='launch_failure')
            self.last_failure=info;self.result['last_command_failure']=info;self.persist();raise CommandFailure(info) from None
        event={'stage':self.stage,'command_id':identity,'exit_code':p.returncode}
        self.result['command_events']=(self.result['command_events']+[event])[-256:]
        if p.returncode:
            info=diagnostic(self.stage,identity,p.returncode,p.stderr);self.last_failure=info
            self.result['last_command_failure']=info;self.persist();raise CommandFailure(info)
        self.persist();return p.stdout
    def json(self,*args,**kw):return json.loads(self.call(*args,**kw))
    def create(self,kind,image,*args,command):
        require(isinstance(command,list) and command,'explicit_container_command_required')
        cid=self.call('create','--pull','never','--name','abap-rehearsal-'+self.run+'-'+kind,
            '--label','com.abap.rehearsal='+self.run,'--label','com.abap.rehearsal.kind='+kind,
            '--restart','no','--log-driver','local','--log-opt','max-size=256k','--log-opt','max-file=1',
            '--log-opt','compress=false',*args,image,*command).decode().strip()
        require(len(cid)==64 and all(c in '0123456789abcdef' for c in cid),'invalid_disposable_container_id')
        self.owned[cid]=kind;return cid
    def inspect_owned(self,cid,network,readonly):
        info=self.json('inspect',cid)[0];labels=info.get('Config',{}).get('Labels') or {};host=info['HostConfig']
        require(info['Id']==cid and labels.get('com.abap.rehearsal')==self.run and labels.get('com.abap.rehearsal.kind')==self.owned[cid],
            'disposable_container_identity_mismatch')
        require(host.get('NetworkMode')==network and host.get('ReadonlyRootfs') is readonly and not host.get('Privileged')
            and not host.get('PortBindings') and not host.get('Binds') and host.get('PidMode')!='host'
            and host.get('IpcMode')!='host' and host.get('RestartPolicy',{}).get('Name')=='no','disposable_container_isolation_failed')
        require(all(m.get('Type')=='tmpfs' for m in info.get('Mounts',[])),'unexpected_persistent_container_mount')
        require('ALL' in (host.get('CapDrop') or []) and any(v.startswith('no-new-privileges') for v in host.get('SecurityOpt') or []),
            'disposable_container_privilege_guard_failed')
        return info
    def cleanup(self):
        failures=[];previous=self.stage;self.stage='container_cleanup'
        for cid in reversed(list(self.owned)):
            try:
                info=self.json('inspect',cid)[0]
                require(info['Id']==cid and (info['Config'].get('Labels') or {}).get('com.abap.rehearsal')==self.run,'cleanup_identity_mismatch')
                self.call('rm','-f','-v',cid);del self.owned[cid]
            except BaseException as error:failures.append(failure(error,self.stage,self.last_failure))
        result={'status':'PASS' if not failures else 'BLOCKED','remaining_owned_containers':len(self.owned),'errors':failures}
        self.result['cleanup_attempts'].append(result);self.stage=previous;self.persist();return result
    def capture_states(self):
        states={}
        for cid,kind in self.owned.items():
            try:
                info=self.json('inspect',cid)[0]
                require(info['Id']==cid and (info['Config'].get('Labels') or {}).get('com.abap.rehearsal')==self.run,'diagnostic_container_identity_mismatch')
                state=info.get('State',{})
                states[kind]={'running':bool(state.get('Running')),'exit_code':state.get('ExitCode'),
                    'oom_killed':bool(state.get('OOMKilled')),'dead':bool(state.get('Dead'))}
                try:
                    log=subprocess.run([*self.prefix,'logs','--tail','80',cid],capture_output=True,timeout=5)
                    states[kind]['log_category']=diagnostic('capture_container_state','docker_logs',log.returncode,(log.stdout+log.stderr)[-65536:])
                except subprocess.TimeoutExpired:states[kind]['log_category']={'classification':'timeout','raw_stderr_retained':False}
                except OSError:states[kind]['log_category']={'classification':'launch_failure','raw_stderr_retained':False}
            except BaseException as error:states[kind]={'diagnostic':failure(error,'capture_container_state')}
        return states

READINESS_PROBE=r'''import json,urllib.request,socket
results={}
for path in ['/health','/ready','/login']:
 with urllib.request.urlopen('http://127.0.0.1:8000'+path,timeout=5) as response:
  data=response.read(200000);results[path]=response.status
  if path=='/health':assert json.loads(data)['status']=='healthy'
  if path=='/ready':assert json.loads(data)['status']=='ready'
assert all(v==200 for v in results.values())
routes=open('/proc/net/route').read().splitlines()[1:]
assert not any(line.split()[1]=='00000000' for line in routes)
s=socket.socket();s.settimeout(1)
try:
 result=s.connect_ex(('192.0.2.1',443));assert result!=0
finally:s.close()
print(json.dumps({'status':'PASS','http_statuses':results,'default_route':False,'outbound_connection_blocked':True}))
'''

ROLE_PROBE=r'''import os,json,psycopg
with psycopg.connect(os.environ['DATABASE_URL']) as c:
 assert c.execute('SHOW transaction_read_only').fetchone()[0]=='on'
 assert c.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication FROM pg_roles WHERE rolname=current_user").fetchone()==(False,False,False,False)
 assert c.execute("SELECT has_table_privilege(current_user,'employees','INSERT'),has_table_privilege(current_user,'employees','UPDATE'),has_schema_privilege(current_user,'public','CREATE')").fetchone()==(False,False,False)
print('{"status":"PASS-readonly-database-role"}')
'''

def run_recovered(docker,app_image,db_image,original_environment,dump,expected_app_ids,expected_layers,expected_migrations):
    started=time.monotonic();result=docker.result;admin_password=secrets.token_hex(32);reader_password=secrets.token_hex(32)
    try:
        docker.begin('inspect_recovered_image')
        image=docker.json('image','inspect',app_image)[0]
        require(image['Id'] in expected_app_ids and image.get('RootFS',{}).get('Layers')==expected_layers,'imported_image_identity_or_layers_mismatch')
        require(all(row.split('=',1)[0] in BASE_ENV_KEYS for row in image.get('Config',{}).get('Env',[])),'image_default_environment_requires_review')
        result['image_restoration']={'status':'PASS','imported_image_id':image['Id'],'layer_count':len(expected_layers)}
        docker.complete();docker.begin('create_postgresql')
        # PostgreSQL data/WAL and all application writable paths live in bounded RAM.
        db=docker.create('database',db_image,'--network','none','--read-only','--cpus','0.75','--memory','768m','--pids-limit','160',
            '--cap-drop','ALL','--cap-add','CHOWN','--cap-add','DAC_OVERRIDE','--cap-add','FOWNER','--cap-add','SETGID','--cap-add','SETUID',
            '--security-opt','no-new-privileges','--shm-size','128m',
            '--tmpfs','/var/lib/postgresql:rw,nosuid,nodev,size=256m','--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16m',
            '-e','POSTGRES_DB=abap_recovered','-e','POSTGRES_USER=rehearsal_admin','-e','POSTGRES_PASSWORD='+admin_password,
            '--entrypoint','docker-entrypoint.sh',command=['postgres','-c','listen_addresses=127.0.0.1',
                '-c','shared_buffers=64MB','-c','max_connections=20','-c','autovacuum=off','-c','shared_preload_libraries='])
        docker.inspect_owned(db,'none',True);docker.complete();docker.begin('start_postgresql');docker.call('start',db);docker.complete();docker.begin('wait_postgresql')
        deadline=time.monotonic()+90
        while True:
            try:docker.call('exec',db,'pg_isready','-U','rehearsal_admin','-d','abap_recovered',timeout=5);break
            except Blocked:
                require(docker.inspect_owned(db,'none',True).get('State',{}).get('Running'),'isolated_postgresql_exited_before_ready')
                require(time.monotonic()<deadline,'isolated_postgresql_startup_timeout');time.sleep(1)
        version=docker.call('exec',db,'postgres','--version').decode();require('PostgreSQL) 18.' in version,'isolated_postgresql_major_mismatch')
        docker.complete();docker.begin('restore_postgresql_archive')
        # Empty disposable database only; restore does not invoke any ABAP migration runner.
        docker.call('exec','-i',db,'pg_restore','--exit-on-error','--single-transaction','--no-owner','--no-privileges',
            '-U','rehearsal_admin','--dbname','abap_recovered',data=dump,timeout=180)
        result['database_archive_restore']={'status':'PASS'};docker.complete();docker.begin('verify_restored_schema')
        query=b'SELECT migration_name FROM schema_migrations ORDER BY migration_name;'
        ledger=docker.call('exec','-i',db,'psql','-XAt','-v','ON_ERROR_STOP=1','-U','rehearsal_admin','-d','abap_recovered',data=query).decode().splitlines()
        require(ledger==expected_migrations and not any(name.startswith(('014_','015_','016_')) for name in ledger),'restored_migration_ledger_mismatch')
        schema_query=b"SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('employees','users','customers','invoices','workflow_executions','schema_migrations','public_rag_usage_counters'); SELECT count(*) FROM pg_constraint WHERE contype='f' AND NOT convalidated;"
        schema=docker.call('exec','-i',db,'psql','-XAt','-v','ON_ERROR_STOP=1','-U','rehearsal_admin','-d','abap_recovered',data=schema_query).decode().splitlines()
        require(schema==['7','0'],'restored_schema_contract_or_foreign_key_validation_failed')
        result['database_restoration']={'status':'PASS','postgresql_major':18,'migration_records':len(ledger),
            'required_relations':7,'unvalidated_foreign_keys':0,'assistant_migrations_applied':False}
        docker.complete();docker.begin('configure_readonly_role')
        sql=("CREATE ROLE rehearsal_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '"+reader_password+"';\n"
            "GRANT CONNECT ON DATABASE abap_recovered TO rehearsal_reader; GRANT USAGE ON SCHEMA public TO rehearsal_reader;\n"
            "REVOKE CREATE ON SCHEMA public FROM PUBLIC; REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;\n"
            "GRANT SELECT ON ALL TABLES IN SCHEMA public TO rehearsal_reader;\n"
            "ALTER ROLE rehearsal_reader SET default_transaction_read_only=on;\n").encode()
        docker.call('exec','-i',db,'psql','-Xq','-v','ON_ERROR_STOP=1','-U','rehearsal_admin','-d','abap_recovered',data=sql)
        docker.complete();docker.begin('create_application')
        environment=safe_environment(original_environment,reader_password)
        args=['--network','container:'+db,'--read-only','--cpus','0.5','--memory','384m','--pids-limit','96',
            '--cap-drop','ALL','--security-opt','no-new-privileges','--user','10001:10001',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16m,uid=10001,gid=10001',
            '--tmpfs','/app/logs:rw,nosuid,nodev,noexec,size=16m,uid=10001,gid=10001',
            '--tmpfs','/app/data/documents:rw,nosuid,nodev,noexec,size=16m,uid=10001,gid=10001']
        for key,value in sorted(environment.items()):args+=['-e',key+'='+value]
        # Entrypoint Python imports factory directly; never deployment's __main__/migrate.
        args+=['--entrypoint','python']
        app=docker.create('application',app_image,*args,command=['-m','uvicorn','deployment:create_application','--factory','--host','127.0.0.1','--port','8000','--no-proxy-headers'])
        info=docker.inspect_owned(app,'container:'+db,True)
        require(info['Config'].get('Cmd')==['-m','uvicorn','deployment:create_application','--factory','--host','127.0.0.1','--port','8000','--no-proxy-headers'],
            'unexpected_application_startup_command')
        docker.complete();docker.begin('start_application');docker.call('start',app);docker.complete();docker.begin('wait_application_readiness');deadline=time.monotonic()+90
        while True:
            try:
                probe=json.loads(docker.call('exec',app,'python','-c',READINESS_PROBE,timeout=15));break
            except Blocked:
                require(docker.inspect_owned(app,'container:'+db,True).get('State',{}).get('Running'),'recovered_application_exited_before_ready')
                require(time.monotonic()<deadline,'recovered_application_readiness_timeout');time.sleep(1)
        result['application_startup']={'status':'PASS','image_unchanged':True,'database_role_readonly':True,'workers_started':False}
        result['health_readiness']=probe;docker.complete();docker.begin('verify_readonly_role')
        require(json.loads(docker.call('exec',app,'python','-c',ROLE_PROBE))['status']=='PASS-readonly-database-role','readonly_database_role_verification_failed')
        result['health_readiness']=probe
        result['configuration_recovery']={'status':'PASS-with-documented-isolation-overrides','production_secrets_mounted':False,'external_integrations_enabled':False}
        docker.complete();docker.begin('final_container_verification')
        final=docker.call('exec','-i',db,'psql','-XAt','-v','ON_ERROR_STOP=1','-U','rehearsal_admin','-d','abap_recovered',data=query).decode().splitlines()
        require(final==ledger,'migration_ledger_changed_during_rehearsal')
        docker.inspect_owned(app,'container:'+db,True);docker.inspect_owned(db,'none',True)
        result['isolation']={'status':'PASS','published_ports':False,'persistent_production_mounts':False,'network':'loopback-only shared disposable namespace'}
        docker.complete()
        result['status']='PASS-isolated-application-rehearsal';result['duration_seconds']=round(time.monotonic()-started,3)
    except BaseException as error:
        result.update(status='FAIL-or-BLOCKED-rehearsal',failure=failure(error,docker.stage,docker.last_failure),failed_stage=docker.stage)
        result['container_states']=docker.capture_states()
    finally:result['cleanup']=docker.cleanup()
    result['duration_seconds']=round(time.monotonic()-started,3)
    if result['cleanup']['status']!='PASS' and result.get('status')=='PASS-isolated-application-rehearsal':result['status']='BLOCKED-container-cleanup'
    docker.persist()
    return result
