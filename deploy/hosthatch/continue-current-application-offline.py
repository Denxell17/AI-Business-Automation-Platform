#!/usr/bin/env python3
"""Offline continuation: SEPARATE execution approval required; preparation never runs it.

Two namespaces, private Docker store/socket, no published ports and RAM-only DB data.
Never use production Compose or load artifacts into the production daemon.
"""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid

ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-offline-app-continuation-20261104-1.json'
IMAGE_SNAPSHOT='6980ad9af5cd4281a5a1e88e1d5f6470a615d675384ad6d7b61810ef548fcf06'
CONFIG_SNAPSHOT='a6cf741f6bc5cdeaf0016b698bf77b0f651ffbb521c760796869418953a5a848'
DB_SNAPSHOT='ac2dae86ca8f5106bfcb4c08a57aa8e1afec77496ab0cfb3e010fd087cd55e45'
IMAGE_SHA='36ee387eb1c96d3032586a05cab800081308e4003f6a369c197d386f08cca179'
CONFIG_SHA='2281312dbb691abe693dfb2467361e951624c840654c126bbe64958c76e5d0d8'
DB_SHA='25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761'
PRESERVER_SHA='4c39dc201b246a99a0d4b608b5961cb44bfc1570ec9cbdde3697682e427933b6'
CORE_SHA='30ab84e8ac45c28dfdeb9c466f6e47c18ebf214216cbf494df90870f77dbd0f6'
COLLECTOR_SHA='f1bb60cba42c3befa386581c7e7903d0e0c42a67571c1051c7b582d78fc249c3'
DIAGNOSTICS=None
ENV={'PATH':'/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/nonexistent','LC_ALL':'C',
     'GOMAXPROCS':'1','GOMEMLIMIT':'256MiB'}
MIGRATIONS=['001_initial_schema.sql','002_correct_schema_contract.sql','003_create_agent_templates.sql',
 '004_create_agent_executions.sql','005_create_webhook_delivery_state.sql','006_create_crm_domain.sql',
 '007_create_invoice_document_domain.sql','008_add_user_session_version.sql','009_add_user_interface_language.sql',
 '010_add_workflow_n8n_outbox_controls.sql','011_add_n8n_demo_event_acceptance.sql',
 '012_move_n8n_callback_authority.sql','013_create_public_rag_usage_counters.sql']
class Blocked(Exception):pass
def require(value,code):
    if not value:
        error=Blocked(code);error.safe_code=code;raise error
def sha(data):return hashlib.sha256(data).hexdigest()

def recovery_inputs(cache):
    # Image import already passed. Reuse that same immutable cached image if its
    # original transport archive was cleaned; configuration/dump require exact bytes.
    inputs={Path(row['path']).name:Path(row['path']) for row in cache['candidates'] if row['exact_preserved_hash_matches']}
    require({'application-configuration.tar','database.dump'}<=set(inputs),'verified_local_artifacts_missing_no_download_authorized')
    return inputs
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def run(*args,timeout=45,stage='rehearsal_control'):
    identity='control_'+Path(args[0]).name if Path(args[0]).name in {'mount','umount','ip','dockerd'} else 'control_operation'
    try:p=subprocess.run(list(args),stdin=subprocess.DEVNULL,capture_output=True,env=ENV,timeout=timeout)
    except subprocess.TimeoutExpired as error:
        if DIAGNOSTICS:raise DIAGNOSTICS.CommandFailure(DIAGNOSTICS.diagnostic(stage,identity,stderr=error.stderr or b'',timeout=timeout)) from None
        raise Blocked('rehearsal_control_timeout') from None
    if p.returncode:
        if DIAGNOSTICS:raise DIAGNOSTICS.CommandFailure(DIAGNOSTICS.diagnostic(stage,identity,p.returncode,p.stderr))
        raise Blocked('rehearsal_control_failed_raw_output_suppressed')
    return p.stdout
def write(path,data,mode=0o600):
    with os.fdopen(os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,mode),'wb') as f:f.write(data)
def checkpoint(path,result):
    data=json.dumps(result,indent=2).encode();require(len(data)<=262144,'sanitized_report_capacity_limit')
    temporary=path.with_name(path.name+'.next')
    with os.fdopen(os.open(temporary,os.O_CREAT|os.O_TRUNC|os.O_WRONLY|os.O_NOFOLLOW,0o600),'wb') as f:
        os.fchmod(f.fileno(),0o600);f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(temporary,path)
def error_diagnostic(core,error,stage):
    info=core.failure(error,stage)
    if isinstance(error,Blocked):info.update(classification='guard_failure',code=core.safe_id(getattr(error,'safe_code','unclassified_guard_failure')))
    return info
def postflight(helper,baseline):
    """Independent read-only comparisons, even after a failed operation/deadline."""
    result={};previous=helper.DEADLINE;helper.DEADLINE=time.monotonic()+120
    try:
        try:result['production_state']={'status':'PASS' if helper.inventory()[0]==baseline else 'FAIL'}
        except BaseException:result['production_state']={'status':'BLOCKED','reason':'readonly_comparison_unavailable'}
    finally:helper.DEADLINE=previous
    result['status']='PASS' if all(v['status']=='PASS' for v in result.values()) else 'FAIL' if any(v['status']=='FAIL' for v in result.values()) else 'BLOCKED'
    return result
def owned_root(root):
    s=root.lstat();require(root.parent==ROOT and root.name.startswith('app-rehearsal-') and root.resolve()==root
        and stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'unsafe_owned_rehearsal_root');return(s.st_dev,s.st_ino)
def tmpfs_identity(path):
    rows=[line.split() for line in Path('/proc/self/mountinfo').read_text().splitlines() if line.split()[4]==str(path)]
    require(len(rows)==1 and rows[0][rows[0].index('-')+1]=='tmpfs','owned_sensitive_mount_identity_mismatch')
    return rows[0][0],rows[0][2]

def integrity_docker(core):
    """Add a corruption check only inside the disposable restored database."""
    class IntegrityDocker(core.Docker):
        def complete(self):
            finished=self.stage
            super().complete()
            if finished=='verify_restored_schema':
                self.begin('verify_database_integrity')
                databases=[cid for cid,kind in self.owned.items() if kind=='database']
                require(len(databases)==1,'disposable_integrity_database_identity_ambiguous')
                try:self.call('exec',databases[0],'pg_amcheck','--no-password','--install-missing','--heapallindexed',
                    '--username=rehearsal_admin','--database=abap_recovered',timeout=60)
                except core.CommandFailure as error:
                    error.diagnostic['command_id']='docker_exec_pg_amcheck';raise
                self.result['database_integrity']={'status':'PASS','tool':'pg_amcheck','scope':'disposable restored database only'}
                super().complete()
    return IntegrityDocker
def inner(root):
    global DIAGNOSTICS
    owned_root(root);spec=json.loads((root/'sensitive/spec.json').read_bytes())
    require(os.getpid()==1 and os.readlink('/proc/self/ns/net')!=spec['host_network_namespace']
        and os.readlink('/proc/self/ns/mnt')!=spec['host_mount_namespace'],'private_namespace_precondition_failed')
    core=load(root/'application_rehearsal_core.py','isolated_core')
    DIAGNOSTICS=core
    # Mask the host daemon sockets only inside this private mount namespace.
    targets={Path(p).resolve() for p in ['/run/docker.sock','/var/run/docker.sock','/run/containerd/containerd.sock','/run/docker/containerd/containerd.sock'] if Path(p).exists()}
    for target in targets:
        run('/usr/bin/mount','--bind','/dev/null',str(target),stage='mask_host_sockets')
        require(not stat.S_ISSOCK(target.stat().st_mode),'host_docker_socket_not_hidden')
    run('/usr/bin/mount','-t','tmpfs','-o','size=32m,mode=0755,nodev,nosuid','tmpfs','/run',stage='private_runtime_paths')
    run('/usr/sbin/ip','link','set','dev','lo','up',stage='enable_private_loopback')
    require(not run('/usr/sbin/ip','route','show').strip() and not run('/usr/sbin/ip','-6','route','show','default').strip(),'unexpected_isolated_network_route')
    private=root/'private';private.mkdir(mode=0o700)
    config=core.daemon_configuration(private,spec['run']);write(private/'daemon.json',json.dumps(config).encode())
    run('/usr/bin/dockerd','--validate','--config-file',str(private/'daemon.json'),stage='validate_private_daemon_configuration')
    docker=integrity_docker(core)(['/usr/bin/docker','--host','unix://'+str(private/'docker.sock')],spec['run'],
        checkpoint=lambda value:checkpoint(root/'sensitive/progress.json',value))
    log=(root/'sensitive/daemon.log').open('xb')
    daemon=None;result=docker.result
    try:
        docker.begin('start_private_daemon')
        try:daemon=subprocess.Popen(['/usr/bin/dockerd','--config-file',str(private/'daemon.json')],stdin=subprocess.DEVNULL,stdout=log,stderr=log,env=ENV)
        except OSError:raise core.CommandFailure(core.diagnostic(docker.stage,'private_daemon_start',classification='launch_failure')) from None
        docker.complete()
        docker.begin('wait_private_daemon')
        deadline=time.monotonic()+90
        while True:
            require(daemon.poll() is None,'private_daemon_exited')
            try:docker.call('version','--format','{{.Server.Version}}',timeout=5);break
            except core.CommandFailure:
                require(time.monotonic()<deadline,'private_daemon_start_timeout');time.sleep(1)
        docker.complete();docker.begin('load_application_image')
        # Both loads target only the private endpoint/store. Original tags never reach host Docker.
        docker.call('load',data=(root/'application-image.tar').read_bytes(),timeout=240)
        result['application_image_import']={'status':'PASS'};docker.complete();docker.begin('load_postgresql_image')
        docker.call('load',data=(root/'postgres-image.tar').read_bytes(),timeout=240)
        result['postgresql_image_import']={'status':'PASS'};docker.complete()
        result=core.run_recovered(docker,spec['app_config_digest'],spec['db_config_digest'],spec['environment'],
            (root/'sensitive/database.dump').read_bytes(),{spec['app_image_id'],spec['app_config_digest']},spec['app_layers'],MIGRATIONS)
        result['image_load']={'status':'PASS','separate_daemon_and_store':True,'production_tags_modified':False}
    except BaseException as error:
        result.update(status='FAIL-or-BLOCKED-rehearsal',failure=error_diagnostic(core,error,docker.stage),failed_stage=docker.stage)
        result['container_states']=docker.capture_states()
    finally:
        # Never replace an earlier failed cleanup with a second empty success.
        result['container_cleanup']=docker.result['cleanup_attempts'][-1] if docker.result['cleanup_attempts'] else docker.cleanup()
        try:
            if daemon and daemon.poll() is None:
                daemon.terminate()
                try:daemon.wait(timeout=30)
                except subprocess.TimeoutExpired:daemon.kill();daemon.wait(timeout=10)
            result['daemon_cleanup']={'status':'PASS','exit_code':daemon.returncode if daemon else None,'started':daemon is not None}
        except BaseException:result['daemon_cleanup']={'status':'BLOCKED','reason':'owned_daemon_stop_failed'}
        log.close()
        if result.get('status')!='PASS-isolated-application-rehearsal':
            try:
                with (root/'sensitive/daemon.log').open('rb') as stream:
                    stream.seek(0,2);size=stream.tell();stream.seek(max(0,size-65536));tail=stream.read(65536)
                result['daemon_log_category']=core.diagnostic('private_daemon','daemon_log',stderr=tail)
                result['daemon_log_category']['source_bytes']=size
            except BaseException:result['daemon_log_category']={'stderr_category':'unavailable'}
        if result['container_cleanup']['status']!='PASS' or result['daemon_cleanup']['status']!='PASS':result['status']='BLOCKED-private-cleanup'
        checkpoint(root/'sensitive/result.json',result)
    return result

PRODUCTION_IMAGE='sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49'

def main():
    global DIAGNOSTICS
    require(sys.argv[1:]==['--execute-approved-continuation'] and os.geteuid()==0,'separate_approved_authenticated_sudo_required')
    os.umask(0o077);os.nice(15)
    require(ROOT.resolve()==ROOT and ROOT.is_dir() and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'unsafe_receipt_parent')
    require(not RECEIPT.exists() and not RECEIPT.is_symlink(),'rehearsal_already_reserved_do_not_repeat')
    for binary in ['/usr/bin/unshare','/usr/bin/mount','/usr/bin/umount','/usr/bin/dockerd','/usr/bin/docker','/usr/sbin/ip']:
        require(Path(binary).is_file(),'required_rehearsal_binary_missing')
    siblings=Path(__file__).resolve().parent
    require(sha((siblings/'preserve-current-app-once.py').read_bytes())==PRESERVER_SHA,'preservation_helper_checksum_mismatch')
    require(sha((siblings/'application_rehearsal_core.py').read_bytes())==CORE_SHA,'rehearsal_core_checksum_mismatch')
    p=load(siblings/'preserve-current-app-once.py','verified_preserver');core=load(siblings/'application_rehearsal_core.py','reviewed_core')
    DIAGNOSTICS=core
    p.DEADLINE=time.monotonic()+2400
    baseline,rows=p.inventory();require(p.service(rows,'web')['Image']==PRODUCTION_IMAGE and p.service(rows,'database')['Image']==p.DB_IMAGE,'production_release_drift')
    disk=shutil.disk_usage(ROOT).free
    memory=next((int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')),0)
    require(disk>=8_000_000_000 and memory>=2_000_000_000,'rehearsal_resource_reserve_insufficient')
    collector_path=siblings/'assistant-release-finalization-readonly.py'
    require(sha(collector_path.read_bytes())==COLLECTOR_SHA,'readonly_collector_checksum_mismatch')
    collector=load(collector_path,'offline_cache_reader')
    cache=collector.cached_artifacts()
    inputs=recovery_inputs(cache)
    receipt={'operation':'approved-offline-app-continuation-20261104-1','status':'reserved','stage':'workspace_setup','production_services_modified':False,
        'snapshots_created_or_deleted':False,'n8n_drills_repeated':False,'migrations_014_016_applied':False}
    receipt['baseline']={'production_state_sha256':sha(json.dumps(baseline,sort_keys=True).encode())}
    write(RECEIPT,json.dumps(receipt).encode())
    identifier=uuid.uuid4().hex[:16];root=ROOT/('app-rehearsal-'+identifier)
    cgroup=Path('/sys/fs/cgroup')/('abap-rehearsal-'+identifier)
    require(not cgroup.exists(),'disposable_cgroup_name_already_exists')
    root.mkdir(mode=0o700);identity=owned_root(root)
    receipt.update(disposable_directory=str(root),directory_identity=identity,run_id=identifier)
    with os.fdopen(os.open(RECEIPT,os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW),'w') as f:json.dump(receipt,f)
    sensitive=root/'sensitive';sensitive.mkdir(mode=0o700);mounted=False;mount_identity=None;child=None;cleanup=[];start=time.monotonic()
    try:
        run('/usr/bin/mount','-t','tmpfs','-o','size=128m,mode=0700,nodev,nosuid,noexec','tmpfs',str(sensitive),stage='create_sensitive_tmpfs');mounted=True;mount_identity=tmpfs_identity(sensitive)
        for name in ['continue-current-application-offline.py','application_rehearsal_core.py']:write(root/name,(siblings/name).read_bytes(),0o500)
        receipt['stage']='verify_configuration_artifact';checkpoint(RECEIPT,receipt)
        configuration=inputs['application-configuration.tar'].read_bytes()
        require(sha(configuration)==CONFIG_SHA,'configuration_artifact_digest_mismatch');p.verify_package(configuration,configuration)
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(configuration),mode='r:') as archive:
            runtime=json.load(archive.extractfile('private/runtime.json'))
        receipt['configuration_authentication']={'status':'PASS'};receipt['stage']='verify_database_artifact';checkpoint(RECEIPT,receipt)
        dump=inputs['database.dump'].read_bytes()
        require(sha(dump)==DB_SHA and dump.startswith(b'PGDMP'),'database_artifact_digest_mismatch');write(sensitive/'database.dump',dump)
        receipt['database_authentication']={'status':'PASS'};receipt['stage']='verify_application_image_artifact';checkpoint(RECEIPT,receipt)
        if 'application-image.tar' in inputs:
            image=inputs['application-image.tar'].read_bytes()
            require(sha(image)==IMAGE_SHA,'image_artifact_digest_mismatch')
            receipt['image_source']='existing_verified_archive'
        else:
            # Read-only transport of the exact preserved image, not a new backup.
            image=p.docker('image','save',p.IMAGE,max_output=128_000_000,timeout=240)
            receipt['image_source']='cached_exact_preserved_image_readonly_export'
        image_check=p.verify_image(io.BytesIO(image))
        require(image_check['configuration_digest']=='sha256:c0db4f1db35ed23e472768b6c15df0d1c2acef7a31aae2cadebb8908c899bd17'
            and image_check['layers_verified']==10,'preserved_image_configuration_or_layers_mismatch')
        receipt['image_transport_sha256']=sha(image);write(root/'application-image.tar',image)
        del image
        receipt['image_authentication']={'status':'PASS'};receipt['stage']='export_stock_postgresql_image';checkpoint(RECEIPT,receipt)
        postgres=p.docker('image','save',p.DB_IMAGE,max_output=1_000_000_000,timeout=240)
        original=p.IMAGE;p.IMAGE=p.DB_IMAGE
        try:db_check=p.verify_image(io.BytesIO(postgres))
        finally:p.IMAGE=original
        write(root/'postgres-image.tar',postgres);del postgres
        original_env=p.envmap(runtime['web']['Config'].get('Env'))
        context={'run':identifier,'app_image_id':p.IMAGE,'app_config_digest':image_check['configuration_digest'],
            'db_config_digest':db_check['configuration_digest'],'app_layers':runtime['image']['RootFS']['Layers'],
            'environment':core.safe_environment(original_env,'deferred-isolated-reader-password'),
            'host_network_namespace':os.readlink('/proc/self/ns/net'),'host_mount_namespace':os.readlink('/proc/self/ns/mnt')}
        write(sensitive/'spec.json',json.dumps(context).encode())
        receipt['verified_artifacts']={'previously_verified_image_snapshot':IMAGE_SNAPSHOT,'configuration_snapshot':CONFIG_SNAPSHOT,'database_snapshot':DB_SNAPSHOT,
            'previously_verified_image_archive_sha256':IMAGE_SHA,'current_image_transport_sha256':receipt['image_transport_sha256'],
            'configuration_sha256':CONFIG_SHA,'database_dump_sha256':DB_SHA}
        receipt['stage']='isolated_child_execution';checkpoint(RECEIPT,receipt)
        child=subprocess.Popen(['/usr/bin/unshare','--mount','--net','--pid','--fork','--kill-child=SIGKILL','--mount-proc',
            '--propagation','private','/usr/bin/python3','-I','-B',str(root/'continue-current-application-offline.py'),'--inner',str(root)],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=ENV,start_new_session=True)
        end=time.monotonic()+900
        while child.poll() is None:
            available=next((int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')),0)
            require(time.monotonic()<end and shutil.disk_usage(ROOT).free>=3_500_000_000 and available>=512_000_000,'private_rehearsal_resource_or_time_guard')
            if (sensitive/'progress.json').is_file():
                receipt['rehearsal']=json.loads((sensitive/'progress.json').read_bytes());checkpoint(RECEIPT,receipt)
            print(json.dumps({'event':'isolated_rehearsal_running','stage':receipt.get('rehearsal',{}).get('current_stage','private_namespace_setup'),
                'elapsed_seconds':round(time.monotonic()-start)}),flush=True)
            time.sleep(5)
        require((sensitive/'result.json').is_file(),'private_rehearsal_no_safe_result')
        receipt['rehearsal']=json.loads((sensitive/'result.json').read_bytes())
        receipt['namespace_process_exit_code']=child.returncode
        require(receipt['rehearsal'].get('status')=='PASS-isolated-application-rehearsal','isolated_application_rehearsal_failed')
        receipt.update(status='PASS-isolated-current-application-rehearsal')
    except BaseException as error:
        receipt.update(status='FAIL-or-BLOCKED-isolated-rehearsal',failure=error_diagnostic(core,error,receipt['stage']),failed_stage=receipt['stage'])
    finally:
        # Recover partial progress even if a child failed before its final result.
        if 'rehearsal' not in receipt and (sensitive/'progress.json').is_file():
            try:receipt['rehearsal']=json.loads((sensitive/'progress.json').read_bytes())
            except BaseException:receipt['progress_recovery']='BLOCKED'
        if child:receipt['namespace_process_exit_code']=child.poll()
        saved=True
        try:checkpoint(RECEIPT,receipt)
        except BaseException:cleanup.append('failure_report_checkpoint_blocked');saved=False
        if child and child.poll() is None:
            try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=15)
            except BaseException:cleanup.append('owned_namespace_stop_blocked')
        stopped=child is None or child.poll() is not None
        if mounted and stopped and saved:
            try:
                require(owned_root(root)==identity and tmpfs_identity(sensitive)==mount_identity,'cleanup_root_or_mount_identity_mismatch')
                run('/usr/bin/umount',str(sensitive),stage='cleanup_sensitive_tmpfs');mounted=False
            except BaseException:cleanup.append('sensitive_tmpfs_unmount_blocked')
        if not mounted and stopped and saved:
            try:
                require(owned_root(root)==identity,'cleanup_root_identity_mismatch')
                points=[l.split()[4] for l in Path('/proc/self/mountinfo').read_text().splitlines()]
                require(not any(v==str(root) or v.startswith(str(root)+'/') for v in points),'unexpected_mount_blocks_directory_cleanup')
                shutil.rmtree(root)
            except BaseException:cleanup.append('owned_directory_cleanup_blocked')
        if cgroup.exists() and stopped:
            try:
                require(cgroup.resolve()==cgroup and cgroup.stat().st_uid==0,'owned_cgroup_identity_mismatch')
                cgroup.rmdir() # Only this exact newly named parent, only when empty.
            except BaseException:cleanup.append('owned_cgroup_cleanup_blocked')
        receipt['cleanup']={'status':'PASS' if not cleanup else 'BLOCKED','errors':cleanup}
        if cleanup:receipt['status']='BLOCKED-rehearsal-cleanup'
        receipt['duration_seconds']=round(time.monotonic()-start,3)
        receipt['limits']=['No external integration, email or scheduler functionality tested','No invoice-document or activity-log file payload restored',
            'Ownership/ACLs adapted only in disposable DB; app uses fresh credentials and read-only DB role','No proxy/TLS, host disaster recovery or production rollback exercised']
        receipt['postflight']=postflight(p,baseline)
        receipt['production_state_unchanged']=receipt['postflight']['production_state']['status']=='PASS'
        receipt['snapshot_access']='NOT-PERFORMED-zero-repository-operations'
        if receipt['postflight']['status']!='PASS' and receipt['status']=='PASS-isolated-current-application-rehearsal':receipt['status']='BLOCKED-postflight-comparison'
        receipt['report_persisted']=True
        try:checkpoint(RECEIPT,receipt)
        except BaseException:receipt.update(status='BLOCKED-report-persistence',report_persisted=False)
    return receipt
if __name__=='__main__':
    def interrupted(signum,frame):require(False,'rehearsal_interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    try:
        if len(sys.argv)==3 and sys.argv[1]=='--inner':result=inner(Path(sys.argv[2]))
        else:result=main()
    except BaseException as error:
        result={'status':'BLOCKED-rehearsal','failure':error_diagnostic(DIAGNOSTICS,error,'namespace_setup') if DIAGNOSTICS else
            {'classification':'guard_failure' if isinstance(error,Blocked) else 'internal_error','code':getattr(error,'safe_code','unclassified_error')}}
        if len(sys.argv)==3 and sys.argv[1]=='--inner':
            try:
                target=Path(sys.argv[2]);owned_root(target)
                if not (target/'sensitive/result.json').exists():write(target/'sensitive/result.json',json.dumps(result).encode())
            except BaseException:pass
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result.get('status') in {'PASS-isolated-application-rehearsal','PASS-isolated-current-application-rehearsal'} else 1)
