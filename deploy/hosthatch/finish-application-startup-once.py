#!/usr/bin/env python3
"""Separate approval required: cached-input application startup + read-only evidence.

No repository/provider requests, image imports, integration dispatch or service edits.
Only new, labelled, network-isolated containers are created and removed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import types
import uuid

ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-cached-application-startup-20261104-1.json'
APP='sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9'
CURRENT='sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c'
CORE_SHA='30ab84e8ac45c28dfdeb9c466f6e47c18ebf214216cbf494df90870f77dbd0f6'
DIAG_SHA='4306de307731a5e9ac9d6403bebbb9da1f7776588fc3685393230ef57f093746'
MIGRATIONS=['001_initial_schema.sql','002_correct_schema_contract.sql','003_create_agent_templates.sql',
 '004_create_agent_executions.sql','005_create_webhook_delivery_state.sql','006_create_crm_domain.sql',
 '007_create_invoice_document_domain.sql','008_add_user_session_version.sql','009_add_user_interface_language.sql',
 '010_add_workflow_n8n_outbox_controls.sql','011_add_n8n_demo_event_acceptance.sql',
 '012_move_n8n_callback_authority.sql','013_create_public_rag_usage_counters.sql']

class Stop(Exception):pass
def need(value,code):
    if not value:raise Stop(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def final_server_args(args):
    # The image's temporary initialization server accepts local socket checks.
    # TCP loopback waits for the final server, which is the one web will use.
    if len(args)>=3 and args[0]=='exec' and args[2]=='pg_isready':
        return (*args[:3],'-h','127.0.0.1',*args[3:])
    return args
def load(name,expected):
    path=Path(__file__).resolve().parent/name;data=path.read_bytes()
    need(sha(data)==expected,'reviewed_helper_checksum_mismatch')
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(data,str(path),'exec'),module.__dict__);return module

def persist(report,first=False):
    flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_EXCL if first else os.O_TRUNC)
    with os.fdopen(os.open(RECEIPT,flags,0o600),'w') as f:
        os.fchmod(f.fileno(),0o600);json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())

def run_readonly(*args):
    p=subprocess.run(args,capture_output=True,timeout=20,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
    need(p.returncode==0,'readonly_inspection_unavailable')
    need(len(p.stdout)<=262144,'readonly_output_limit');return p.stdout.decode()

def unit_summary(name):
    raw=run_readonly('/usr/bin/systemctl','show',name,'--no-pager',
        '-p','ActiveState','-p','UnitFileState','-p','Result','-p','ExecMainStatus',
        '-p','ExecStart','-p','ExecStopPost','-p','FragmentPath','-p','DropInPaths',
        '-p','ReadWritePaths','-p','NextElapseUSecRealtime')
    fields=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
    result={k:fields.get(k,'') for k in ['ActiveState','UnitFileState','Result','ExecMainStatus','NextElapseUSecRealtime']}
    for field in ['ExecStart','ExecStopPost']:
        # Never show arguments: service credentials may appear there.
        result[field+'_executables']=re.findall(r'path=(/[A-Za-z0-9_./-]+)',fields.get(field,''))
    for field in ['FragmentPath','DropInPaths','ReadWritePaths']:
        result[field+'_sha256']=sha(fields.get(field,'').encode())
    return result

def backup_evidence():
    report={'repository_requests':0,'backup_jobs_started':0,'units':{}}
    for name in ['n8n-backup.service','n8n-backup.timer']:
        report['units'][name]=unit_summary(name)
    report['installed_files']={}
    for path in ['/usr/local/sbin/n8n-backup','/usr/local/sbin/n8n-ensure-running','/usr/local/lib/abap/n8n_backup_state.py']:
        p=Path(path);s=p.lstat()
        need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022,'untrusted_backup_executable')
        need(s.st_size<131072,'backup_script_size_limit');data=p.read_bytes()
        report['installed_files'][path]={'sha256':sha(data),'mode':oct(stat.S_IMODE(s.st_mode))}
        if path.endswith('n8n-backup'):
            report['refuses_existing_staging']=b'Existing staging retained' in data
            report['full_repository_budget_reads']=data.count(b'operations_restic_raw_bytes')
    p=Path('/var/backups/n8n/staging')
    report['protected_staging']={'exists':p.exists()}
    if p.exists():
        s=p.lstat();need(p.resolve()==p and stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o077,'untrusted_protected_staging')
        report['protected_staging']['nonempty']=next(p.iterdir(),None) is not None
    raw=run_readonly('/usr/bin/journalctl','-u','n8n-backup.service','-n','40','--no-pager','-o','cat').casefold()
    report['journal_categories']=[category for category,text in [
        ('multiple_container_selection','multiple'),('missing_executable','no such file'),
        ('staging_retained','existing staging retained'),('state_checker_failed','critical:'),
        ('repository_limit','cap_exceeded'),('permission_failure','permission denied')] if text in raw]
    report['raw_logs_printed']=False
    return report

LINK_PROBE=r'''import json,os,psycopg
with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=5,options='-c default_transaction_read_only=on -c statement_timeout=5000') as c:
 c.execute('SET TRANSACTION READ ONLY')
 sql="""SELECT count(DISTINCT r.execution_id), count(DISTINCT CASE WHEN e.status='completed' THEN r.execution_id END),
 count(DISTINCT CASE WHEN e.status='completed' AND EXISTS (SELECT 1 FROM webhook_deliveries d WHERE d.correlation_id=e.execution_id AND d.direction='outbound' AND d.status='succeeded') AND EXISTS (SELECT 1 FROM webhook_deliveries d WHERE d.correlation_id=e.execution_id AND d.direction='inbound' AND d.status='accepted') THEN r.execution_id END)
 FROM invoice_workflow_runs r JOIN invoices i USING(invoice_id) JOIN customers c USING(customer_id)
 JOIN leads l ON l.lead_id=c.source_lead_id JOIN workflow_executions e ON e.execution_id=r.execution_id"""
 row=c.execute(sql).fetchone()
 print(json.dumps(dict(zip(['linked_runs','completed_linked_runs','signed_roundtrip_linked_runs'],row))))
'''

def main():
    need(os.geteuid()==0 and sys.argv[1:]==['--approved-cached-startup'],'separate_authenticated_approval_required')
    os.umask(0o077)
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'private_receipt_parent_required')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'single_use_command_consumed')
    diag=load('diagnose-existing-postgresql-restore.py',DIAG_SHA)
    core=load('application_rehearsal_core.py',CORE_SHA)
    need(diag.shutil.disk_usage(ROOT).free>=1000000000,'disk_reserve_required')
    memory=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    need(memory>=1800000000,'memory_reserve_required')
    dump=diag.read_private(ROOT/'recovery-cache/database.dump',diag.DUMP_SIZE)
    need(len(dump)==diag.DUMP_SIZE and sha(dump)==diag.DUMP_SHA,'retained_dump_integrity_failed')
    rows=json.loads(diag.docker('inspect',*diag.docker('ps','-aq').stdout.decode().split()).stdout)
    web=[r for r in rows if r['Config'].get('Labels',{}).get('com.docker.compose.project')=='abap-deploy' and r['Config'].get('Labels',{}).get('com.docker.compose.service')=='web']
    need(len(web)==1 and web[0]['Image']==CURRENT and web[0]['State']['Running'],'current_production_identity_changed')
    image=json.loads(diag.docker('image','inspect',APP).stdout)[0]
    need(image['Id']==APP,'cached_rollback_image_missing')
    need(json.loads(diag.docker('image','inspect',diag.IMAGE).stdout)[0]['Id']==diag.IMAGE,'cached_postgresql_image_missing')
    baseline=diag.inventory()
    report={'operation':'approved-cached-application-startup-20261104-1','status':'running',
        'b2_requests':0,'image_imports':0,'backup_jobs_started':0,'service_changes':False,
        'configuration_scope':'Previously authenticated recovery configuration; fresh isolated values, image defaults only. No configuration download or exact-file recovery recheck.',
        'database_bootstrap':'One load of retained dump required because prior disposable DB was cleaned; no restore diagnostic repeated.'}
    persist(report,True)
    class StartupDocker(core.Docker):
        def call(self,*args,**kwargs):return super().call(*final_server_args(args),**kwargs)
    docker=StartupDocker(['/usr/bin/docker','--host','unix:///var/run/docker.sock'],uuid.uuid4().hex,
        checkpoint=lambda state:(report.update(application=state),persist(report)))
    try:
        try:report['n8n_backup']=backup_evidence()
        except Exception:report['n8n_backup']={'status':'BLOCKED-readonly-inspection-unavailable','repository_requests':0,'backup_jobs_started':0}
        persist(report)
        try:
            linked=json.loads(diag.docker('exec','-i',web[0]['Id'],'python','-c',LINK_PROBE).stdout)
            need(set(linked)=={'linked_runs','completed_linked_runs','signed_roundtrip_linked_runs'} and
                 all(isinstance(n,int) and n>=0 for n in linked.values()),'invalid_link_evidence')
            report['linked_demo_counts']=linked
        except Exception:report['linked_demo_counts']={'status':'BLOCKED-readonly-query-unavailable'}
        env=dict(v.split('=',1) for v in image['Config'].get('Env',[]))
        report['application']=core.run_recovered(docker,APP,diag.IMAGE,env,dump,{APP},image['RootFS']['Layers'],MIGRATIONS)
        report['status']='PASS-application-startup-continuation' if report['application']['status']=='PASS-isolated-application-rehearsal' else 'BLOCKED-application-startup'
    except BaseException as error:
        report.update(status='BLOCKED-continuation',failure=core.failure(error,docker.stage,docker.last_failure))
    finally:
        for name in ['SIGINT','SIGTERM','SIGHUP']:
            if hasattr(signal,name):signal.signal(getattr(signal,name),signal.SIG_IGN)
        if docker.owned:report['cleanup']=docker.cleanup()
        else:report['cleanup']=docker.result['cleanup_attempts'][-1] if docker.result['cleanup_attempts'] else {'status':'PASS-no-container-created'}
        try:report['production_state_preservation']='PASS' if diag.inventory()==baseline else 'FAIL'
        except Exception:report['production_state_preservation']='BLOCKED'
        if not report['cleanup']['status'].startswith('PASS') or report['production_state_preservation']!='PASS':report['status']='BLOCKED-cleanup-or-production-comparison'
        persist(report)
    return report

if __name__=='__main__':
    for name in ['SIGTERM','SIGHUP']:
        if hasattr(signal,name):signal.signal(getattr(signal,name),lambda *_:(_ for _ in ()).throw(Stop('operator_interrupted')))
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-before-startup','code':str(error) if isinstance(error,Stop) else 'prerequisite_unavailable'}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('PASS') else 1)
