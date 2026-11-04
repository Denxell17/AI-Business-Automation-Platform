"""One new linked acceptance scenario in cached, disposable LOCAL Docker services.

No production endpoints, provider APIs, B2, image builds/pulls or live credentials.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import re
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
APP='sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c'
PG='sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280'
N8N='sha256:240eaa2a3d491adac5817aa4c3f1c521bb18ec79f6e448517158d5220ee0f37b'
BOOT=r'''
import os,sys,time,psycopg
sys.path.insert(0,os.getcwd())
assert '/abap_linked' in os.environ['DATABASE_URL'] and '@database:' in os.environ['DATABASE_URL']
deadline=time.monotonic()+60
while True:
 try:
  with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=2):pass
  break
 except psycopg.OperationalError:
  if time.monotonic()>deadline:raise RuntimeError('fixture_database_not_ready') from None
  time.sleep(.5)
from postgresql_migrations import apply_postgresql_migrations
apply_postgresql_migrations(os.environ['DATABASE_URL'])
from user_service import register_user_account
assert register_user_account('PortfolioAdmin',os.environ['FIXTURE_PASSWORD'],'admin')
from web_app import create_web_application
import uvicorn
uvicorn.run(create_web_application(session_secret=os.environ['ABAP_SESSION_SECRET'],secure_cookies=False),host='0.0.0.0',port=8000,access_log=False)
'''
CASE=r'''
import os,json,time,urllib.request,urllib.parse,http.cookiejar,re
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
assert '/abap_linked' in os.environ['DATABASE_URL'] and '@database:' in os.environ['DATABASE_URL']
from database import load_user_account_by_username,get_database_connection
from crm_service import create_lead,update_lead,convert_lead
from invoice_service import create_invoice,generate_invoice_document
from document_storage import PrivateFileSystemDocumentStorage
from workflow_service import create_workflow,create_workflow_task,update_workflow,create_workflow_schedule
from workflow_worker import run_worker_cycle
from worker_config import load_worker_settings
from integration_config import load_integration_settings
from webhook_retry_worker import run_webhook_retry_cycle
from invoice_repository import link_invoice_workflow_run
from schedule_service import DEFAULT_WORKFLOW_TIME_ZONE
a=load_user_account_by_username('PortfolioAdmin')
lead=create_lead(a,'Fictional Portfolio Lead','demo@example.invalid','','Fictional ABAP Demo',a['user_id'])
for stage in ['contacted','qualified']:
 assert update_lead(a,lead,'Fictional Portfolio Lead','demo@example.invalid','','Fictional ABAP Demo',stage,a['user_id'])
customer=convert_lead(a,lead);assert customer
invoice=create_invoice(a,customer,'DEMO-PORTFOLIO-20261104','',[{'description':'Synthetic demonstration only','quantity':'1','unit_price':'100.00','tax_rate':'0'}])
doc=generate_invoice_document(a,invoice,PrivateFileSystemDocumentStorage());assert doc
assert create_workflow(a,'WF-PORTFOLIO','Synthetic linked portfolio automation','No customer data or external AI','draft')
assert create_workflow_task(a,'TASK-PORTFOLIO','WF-PORTFOLIO',1,'Synthetic action','No external side effects','manual',True)
assert update_workflow(a,'WF-PORTFOLIO','Synthetic linked portfolio automation','No customer data or external AI','active',n8n_enabled=True)
now=datetime.now(timezone.utc)
assert create_workflow_schedule(a,'SCHED-PORTFOLIO','WF-PORTFOLIO','daily',now.astimezone(ZoneInfo(DEFAULT_WORKFLOW_TIME_ZONE)).strftime('%H:%M'),'',True)
worker=run_worker_cycle(now,load_worker_settings());assert worker['claimed']==1 and worker['started']==1,worker
c=get_database_connection();e=dict(c.execute("SELECT * FROM workflow_executions WHERE workflow_id='WF-PORTFOLIO'").fetchone());c.close()
assert link_invoice_workflow_run(invoice,'WF-PORTFOLIO',e['execution_id'],datetime.now(timezone.utc).isoformat())
with open('/tmp/linked-state.json','w') as f:json.dump({'lead':lead,'customer':customer,'invoice':invoice,'execution_id':e['execution_id'],'worker':worker},f)
outbound=run_webhook_retry_cycle(datetime.now(timezone.utc),load_integration_settings())
if outbound['succeeded']!=1:
 c=get_database_connection();details=[dict(r) for r in c.execute('SELECT status,failure_code,response_status,attempt_count FROM webhook_deliveries').fetchall()];c.close()
 print(json.dumps({'delivery_failure':details,'outbound':outbound}))
 raise RuntimeError('linked_outbound_failed')
deadline=time.monotonic()+100
while True:
 c=get_database_connection();status=c.execute('SELECT status FROM workflow_executions WHERE execution_id=?',(e['execution_id'],)).fetchone()['status'];c.close()
 if status=='completed':break
 assert time.monotonic()<deadline,'signed_callback_timeout'
 time.sleep(1)
jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def page(path):return client.open('http://127.0.0.1:8000'+path,timeout=10).read()
csrf=re.search(rb'name="csrf_token"\s+value="([^"]+)"',page('/login')).group(1).decode()
client.open('http://127.0.0.1:8000/login',urllib.parse.urlencode({'username':'PortfolioAdmin','password':os.environ['FIXTURE_PASSWORD'],'csrf_token':csrf}).encode()).read()
invoice_html=page('/invoices/'+invoice)
assert b'DEMO-PORTFOLIO-20261104' in invoice_html and b'Synthetic linked portfolio automation' in invoice_html and b'completed' in invoice_html.lower()
assert b'Fictional' in page('/customers/'+customer)
workflow_html=page('/workflows/WF-PORTFOLIO');assert b'completed' in workflow_html.lower()
c=get_database_connection()
counts={t:c.execute('SELECT COUNT(*) AS n FROM '+t).fetchone()['n'] for t in ['leads','customers','invoices','invoice_workflow_runs','workflow_schedule_occurrences','workflow_executions','n8n_demo_events']}
deliveries=[dict(r) for r in c.execute('SELECT direction,status,attempt_count FROM webhook_deliveries ORDER BY direction').fetchall()]
assert all(v==1 for v in counts.values()),counts
assert {(r['direction'],r['status']) for r in deliveries}=={('inbound','accepted'),('outbound','succeeded')},deliveries
c.close()
print(json.dumps({'status':'PASS-linked-synthetic-local-demo','counts':counts,'worker':worker,'outbound':outbound,'deliveries':deliveries,
 'authenticated_customer_invoice_workflow_pages':'PASS','protected_pdf_created':True,'real_n8n_callback':'PASS',
 'production_demo_executed':False,'external_ai_requests':0}))
'''

def fixture_configuration(fixture):
    password=secrets.token_urlsafe(32)
    env={'DATABASE_BACKEND':'postgresql','DATABASE_URL':'postgresql://fixture:'+password+'@database:5432/abap_linked',
        'ABAP_SESSION_SECRET':secrets.token_urlsafe(48),'FIXTURE_PASSWORD':secrets.token_urlsafe(32),
        'ABAP_ENVIRONMENT':'integration-test','ABAP_WORKER_ENABLED':'true','ABAP_INTEGRATIONS_ENABLED':'true',
        'ABAP_N8N_PRIVATE_DEVELOPMENT_NETWORK':'true','ABAP_N8N_BASE_URL':'http://n8n:5678',
        'ABAP_N8N_WORKFLOW_PATH':'/webhook/abap-workflow','ABAP_INTEGRATION_ALLOWED_HOSTS':'n8n',
        'ABAP_OUTBOUND_WEBHOOK_SECRET':secrets.token_urlsafe(48),'ABAP_INBOUND_WEBHOOK_SECRET':secrets.token_urlsafe(48),
        'ABAP_ADVANCED_ASSISTANT_ENABLED':'false','ABAP_PUBLIC_RAG_ENABLED':'false','PYTHONDONTWRITEBYTECODE':'1'}
    (fixture/'token').write_text(secrets.token_urlsafe(48));(fixture/'bootstrap.py').write_text(BOOT)
    app={'image':APP,'pull_policy':'never','restart':'no','read_only':True,'cap_drop':['ALL'],
         'security_opt':['no-new-privileges:true'],'environment':env,'mem_limit':'384m','pids_limit':128,
         'tmpfs':['/tmp:rw,nosuid,nodev,size=16m,uid=10001,gid=10001','/app/logs:rw,nosuid,nodev,size=16m,uid=10001,gid=10001','/app/data/documents:rw,nosuid,nodev,size=16m,uid=10001,gid=10001']}
    provider=json.loads(json.dumps(app));provider['environment']={k:env[k] for k in ['DATABASE_URL','ABAP_OUTBOUND_WEBHOOK_SECRET','ABAP_INBOUND_WEBHOOK_SECRET']}
    provider['environment']['ABAP_CALLBACK_URL']='http://web:8000/integrations/webhooks/callback'
    provider['command']=['python','-m','n8n_demo_provider'];provider['secrets']=['abap_n8n_provider_token']
    config={'services':{'database':{'image':PG,'pull_policy':'never','restart':'no','mem_limit':'512m',
        'environment':{'POSTGRES_DB':'abap_linked','POSTGRES_USER':'fixture','POSTGRES_PASSWORD':password},
        'tmpfs':['/var/lib/postgresql:rw,nosuid,nodev,size=256m']},
        'web':{**app,'command':['python','/fixture/bootstrap.py'],'volumes':[str(fixture/'bootstrap.py')+':/fixture/bootstrap.py:ro']},
        'demo-provider':provider,
        'n8n':{'image':N8N,'pull_policy':'never','restart':'no','read_only':True,'mem_limit':'768m','pids_limit':256,
          'environment':{'N8N_DIAGNOSTICS_ENABLED':'false','N8N_PERSONALIZATION_ENABLED':'false','N8N_COMMUNITY_PACKAGES_ENABLED':'false',
            'N8N_PUBLIC_API_DISABLED':'true','N8N_SECURE_COOKIE':'false','N8N_BLOCK_ENV_ACCESS_IN_NODE':'true',
            'N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS':'true','DB_SQLITE_POOL_SIZE':'2','N8N_ENCRYPTION_KEY':secrets.token_urlsafe(48)},
          'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],'secrets':['abap_n8n_provider_token'],
          'tmpfs':['/home/node/.n8n:rw,nosuid,nodev,size=96m,uid=1000,gid=1000','/home/node/.cache:rw,nosuid,nodev,size=32m,uid=1000,gid=1000','/tmp:rw,nosuid,nodev,size=16m,uid=1000,gid=1000','/run/abap-bootstrap:rw,nosuid,nodev,noexec,size=4m,uid=1000,gid=1000,mode=0700'],
          'volumes':[str(ROOT/'examples/n8n')+':/workflows:ro'],'entrypoint':['/bin/sh','-c'],
          'command':['node /workflows/build-demo-credential.mjs /run/secrets/abap_n8n_provider_token /run/abap-bootstrap/credential.json && n8n import:credentials --input=/run/abap-bootstrap/credential.json && rm /run/abap-bootstrap/credential.json && n8n import:workflow --input=/workflows/abap-signed-workflow.json && n8n import:workflow --input=/workflows/abap-signed-processor.json && n8n publish:workflow --id=abapM3Demo000001 && n8n publish:workflow --id=abapM3Demo000002 && n8n start']}},
        'networks':{'default':{'internal':True}},'secrets':{'abap_n8n_provider_token':{'file':str(fixture/'token')}}}
    return config

def main():
    project='abap-linked-'+uuid.uuid4().hex[:12]
    output=ROOT/'output/project-completion-20261104';output.mkdir(parents=True,exist_ok=True)
    fixture=output/project;fixture.mkdir()
    report={'scope':'local synthetic linked acceptance only','status':'running','project':project}
    stage='preflight';last_error={}
    def docker(*args,data=None,timeout=60):
        p=subprocess.run(['docker','--context','desktop-linux',*args],input=data,capture_output=True,timeout=timeout)
        if p.returncode:
            text=p.stderr.decode('utf8','replace')
            last_error.update(exit_code=p.returncode,error_classes=sorted(set(re.findall(r'\b(?:AssertionError|ModuleNotFoundError|ValueError|PermissionError|HTTPError|OperationalError|TimeoutError)\b',text))),
                stdin_lines=re.findall(r'File "<stdin>", line (\d+)',text)[-3:])
            for line in p.stdout.decode('utf8','replace').splitlines():
                try:item=json.loads(line)
                except ValueError:continue
                if isinstance(item,dict) and set(item)=={'delivery_failure','outbound'}:last_error['delivery']=item
            raise RuntimeError('docker_exit_'+str(p.returncode))
        return p.stdout
    def compose(*args,**kwargs):return docker('compose','-p',project,'-f',str(fixture/'compose.json'),*args,**kwargs)
    config=fixture_configuration(fixture)
    path=fixture/'compose.json';path.write_text(json.dumps(config))
    try:
        for image in [APP,PG,N8N]:docker('image','inspect',image)
        stage='start_local_fixture';compose('up','-d','--no-build','--pull','never',timeout=60)
        stage='wait_fixture_readiness';deadline=time.monotonic()+180
        while True:
            try:
                compose('exec','-T','web','python','-c',"import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8000/ready',timeout=2).status==200")
                compose('exec','-T','n8n','node','-e',"fetch('http://127.0.0.1:5678/healthz/readiness').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))")
                break
            except RuntimeError:
                ids=compose('ps','-aq').decode().split()
                if ids:
                    rows=json.loads(docker('inspect',*ids))
                    if any(r['State']['Status']=='exited' and r['State']['ExitCode']!=0 for r in rows):raise RuntimeError('fixture_service_exited')
                if time.monotonic()>deadline:raise RuntimeError('fixture_readiness_timeout')
                time.sleep(2)
        stage='linked_acceptance';raw=compose('exec','-T','web','python','-B','-',data=CASE.encode(),timeout=150)
        report.update(json.loads(raw.decode().splitlines()[-1]))
    except Exception as error:
        report.update(status='BLOCKED-linked-local-demo',failed_stage=stage,failure=str(error) if isinstance(error,RuntimeError) else type(error).__name__,diagnostic=last_error)
    finally:
        if stage=='linked_acceptance' and not report['status'].startswith('PASS'):
            report['cleanup']='DEFERRED-owned-local-fixture-retained-for-diagnosis'
            (output/'linked-demo-result.json').write_text(json.dumps(report,indent=2))
            print(json.dumps(report,indent=2));return 1
        try:
            ids=compose('ps','-aq').decode().split()
            if ids:
                rows=json.loads(docker('inspect',*ids))
                if not all(r['Config']['Labels'].get('com.docker.compose.project')==project for r in rows):raise RuntimeError('cleanup_identity_mismatch')
            compose('down','--volumes','--remove-orphans',timeout=60);report['cleanup']='PASS'
            for name in ['bootstrap.py','token','compose.json']:
                p=fixture/name
                if p.exists():p.unlink()
            if list(fixture.iterdir()):raise RuntimeError('unexpected_fixture_files_retained')
            try:fixture.rmdir()
            except OSError:report['empty_fixture_directory_retained']=True
        except Exception:report.update(cleanup='BLOCKED-task-resources-retained',status='BLOCKED-local-cleanup')
        (output/'linked-demo-result.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return 0 if report['status'].startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
