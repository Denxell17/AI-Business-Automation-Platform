#!/usr/bin/env python3
"""Separate approval: temporary authenticated HTTPS demonstration, then cleanup.

No business database writes, shared n8n changes, image builds/pulls, B2 or AI calls.
One disposable stack; one temporary Caddy route; native production login gate.
"""
import copy
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import ssl
import stat
import subprocess
import sys
import time
import types
import urllib.error
import urllib.request
import uuid

ROOT=Path('/var/backups/abap')
RECEIPT=ROOT/'approved-public-linked-demonstration-20261104-1.json'
CURRENT='sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c'
DOCKER_CONFIG_PATH='/nonexistent/.docker'
LAST_DOCKER_FAILURE=None
class Stop(Exception):pass
def need(value,code):
    if not value:raise Stop(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def write_new(path,data,mode=0o600):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode),'wb') as f:
        os.fchmod(f.fileno(),mode);f.write(data);f.flush();os.fsync(f.fileno())
def save(report,first=False):
    flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_EXCL if first else os.O_TRUNC)
    with os.fdopen(os.open(RECEIPT,flags,0o600),'w') as f:
        os.fchmod(f.fileno(),0o600);json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
def load_module(path,data,name):
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(data,str(path),'exec'),module.__dict__);return module
def docker(*args,data=None,timeout=30):
    global LAST_DOCKER_FAILURE
    try:p=subprocess.run(['/usr/bin/docker','--host','unix:///var/run/docker.sock',*args],input=data,capture_output=True,timeout=timeout,
        env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','DOCKER_CONFIG':DOCKER_CONFIG_PATH,'LC_ALL':'C'})
    except subprocess.TimeoutExpired:
        LAST_DOCKER_FAILURE={'command_id':'docker_'+args[0],'classification':'timeout','timeout_seconds':timeout}
        raise Stop('bounded_docker_timeout') from None
    if p.returncode:
        text=p.stderr.decode('utf8','replace')[:65536]
        LAST_DOCKER_FAILURE={'command_id':'docker_'+args[0],'exit_code':p.returncode,
            'error_classes':sorted(set(re.findall(r'\b(?:AssertionError|ModuleNotFoundError|ValueError|PermissionError|HTTPError|OperationalError|TimeoutError)\b',text))),
            'stdin_lines':re.findall(r'File "<stdin>", line (\d+)',text)[-3:]}
        raise Stop('docker_'+re.sub('[^a-z_]','_',args[0])+'_exit_'+str(p.returncode))
    LAST_DOCKER_FAILURE=None
    need(len(p.stdout)<=1048576,'bounded_output_limit');return p.stdout
def inventory():
    ids=docker('ps','-aq').decode().split();need(len(ids)<100,'inventory_limit')
    return json.loads(docker('inspect',*ids)) if ids else []
def stable(rows,project):
    return sorted((r['Id'],r['Image'],r['State']['Running'],r['RestartCount'],
        sha(json.dumps([r['Config'],r['HostConfig'],r['NetworkSettings']['Networks']],sort_keys=True).encode()))
        for r in rows if r['Config'].get('Labels',{}).get('com.docker.compose.project')!=project)
def origin_https(path):
    """Local ops check; public acceptance still requires the signed-in browser."""
    host='app.dennisbasadre.com';context=ssl.create_default_context()
    connection=http.client.HTTPSConnection(host,timeout=15,context=context);raw=None
    try:
        raw=socket.create_connection(('127.0.0.1',443),timeout=15)
        connection.sock=context.wrap_socket(raw,server_hostname=host)
        connection.request('GET',path,headers={'Host':host})
        response=connection.getresponse();return response.status,response.read(200000)
    except ssl.SSLCertVerificationError:raise Stop('origin_tls_certificate_verification_failed') from None
    except (TimeoutError,socket.timeout):raise Stop('origin_https_timeout') from None
    finally:
        connection.close()
        if raw is not None:raw.close()

def origin_smoke():
    result={}
    for path in ['/health','/ready','/login']:
        result[path]=origin_https(path)[0]
        need(result[path]==200,'origin_'+path.strip('/')+'_status_'+str(result[path]))
    return result
def caddy_command(*args,data=None):
    p=subprocess.run(['/usr/bin/caddy',*args],input=data,capture_output=True,timeout=30,
        env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LC_ALL':'C'})
    need(p.returncode==0,'host_caddy_operation_failed');return p.stdout
def proxy_process():
    p=subprocess.run(['/usr/bin/systemctl','show','caddy','--no-pager','-p','MainPID','-p','ActiveState','-p','ExecStart',
        '-p','IPAddressDeny','-p','PrivateNetwork'],capture_output=True,timeout=5)
    need(p.returncode==0,'host_proxy_state_unavailable')
    fields=dict(line.split('=',1) for line in p.stdout.decode().splitlines() if '=' in line)
    need(fields.get('ActiveState')=='active' and fields.get('MainPID','0').isdigit() and int(fields['MainPID'])>0
         and '--resume' not in fields.get('ExecStart',''),'host_proxy_identity_changed')
    need(not fields.get('IPAddressDeny') and fields.get('PrivateNetwork','no')=='no','host_proxy_network_filter_requires_review')
    return fields['MainPID']
def caddy_config():
    client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with client.open('http://127.0.0.1:2019/config/',timeout=5) as response:raw=response.read(1048577)
    need(len(raw)<=1048576,'proxy_configuration_size_limit');return json.loads(raw)
def caddy_load(config):
    caddy_command('reload','--config','/dev/stdin',data=json.dumps(config).encode())
def private_web_address(cid,project):
    info=json.loads(docker('inspect',cid))[0]
    need(info['Config']['Labels'].get('com.docker.compose.project')==project and not info['HostConfig'].get('PortBindings'),'unsafe_demo_web_identity_or_ports')
    networks=info['NetworkSettings']['Networks'];need(len(networks)==1,'unexpected_demo_network_attachment')
    name,endpoint=next(iter(networks.items()));network=json.loads(docker('network','inspect',name))[0]
    need(network['Internal'] and network['Labels'].get('com.docker.compose.project')==project,'demo_network_not_owned_and_internal')
    address=ipaddress.ip_address(endpoint['IPAddress']);need(address.version==4 and address.is_private and not address.is_loopback,'invalid_private_demo_address')
    return str(address)
def remove_owned_route(config,prefix):
    result=copy.deepcopy(config);found=[]
    for server in result.get('apps',{}).get('http',{}).get('servers',{}).values():
        for index,route in enumerate(server.get('routes',[])):
            if route.get('match')==[{'host':['app.dennisbasadre.com'],'path':[prefix+'/*'],'method':['GET']}]:found.append((server,index))
    need(len(found)==1,'owned_proxy_route_identity_changed')
    server,index=found[0];server['routes'].pop(index);return result

def isolate_database(configuration,run):
    need(re.fullmatch('[0-9a-f]{16}',run),'invalid_database_namespace')
    alias='portfolio-db-'+run
    configuration['services']['database']['networks']={'default':{'aliases':[alias]}}
    for name in ['web','demo-provider']:
        env=configuration['services'][name]['environment']
        need(env['DATABASE_URL'].count('@database:')==1 and env['DATABASE_URL'].endswith('/abap_linked'),'unexpected_fixture_database')
        env['DATABASE_URL']=env['DATABASE_URL'].replace('@database:','@'+alias+':')
    return alias

def main():
    global DOCKER_CONFIG_PATH
    need(os.geteuid()==0 and sys.argv[1:]==['--approved-temporary-https-demo'],'explicit_authenticated_demo_approval_required')
    os.umask(0o077)
    need(ROOT.resolve()==ROOT and ROOT.stat().st_uid==0 and stat.S_IMODE(ROOT.stat().st_mode)==0o700,'private_receipt_parent_required')
    need(not RECEIPT.exists() and not RECEIPT.is_symlink(),'single_use_command_consumed')
    source=Path(__file__).resolve().parent
    raw=(source/'reviewed-manifest.json').read_bytes()
    need(sha(raw)==globals().get('__manifest_sha256__'),'reviewed_manifest_mismatch')
    manifest=json.loads(raw);payload={}
    allowed={'verify_linked_portfolio_demo.py','portfolio_https_demo_support.py',
             'examples/n8n/abap-signed-workflow.json','examples/n8n/abap-signed-processor.json','examples/n8n/build-demo-credential.mjs'}
    need(set(manifest)==allowed,'unexpected_package_inputs')
    for name,expected in manifest.items():
        data=(source/name).read_bytes();need(len(data)<131072 and sha(data)==expected,'reviewed_payload_mismatch');payload[name]=data
    fixture=load_module(source/'verify_linked_portfolio_demo.py',payload['verify_linked_portfolio_demo.py'],'reviewed_fixture')
    support=load_module(source/'portfolio_https_demo_support.py',payload['portfolio_https_demo_support.py'],'reviewed_proxy_support')
    memory=next(int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))
    need(memory>=2500000000 and shutil.disk_usage('/run').free>=100000000,'disposable_resource_capacity_insufficient')
    rows=inventory();webs=[r for r in rows if r['Config'].get('Labels',{}).get('com.docker.compose.project')=='abap-deploy' and r['Config'].get('Labels',{}).get('com.docker.compose.service')=='web']
    need(len(webs)==1 and webs[0]['Image']==CURRENT and webs[0]['State']['Running'],'production_web_identity_changed')
    pid=proxy_process();original=caddy_config();auth=support.auth_dial(original)
    need(auth=='127.0.0.1:8000','existing_public_app_upstream_changed')
    for image in [fixture.APP,fixture.PG,fixture.N8N]:need(json.loads(docker('image','inspect',image))[0]['Id']==image,'cached_fixture_image_missing')
    docker('compose','version')
    baseline_origin=origin_smoke()
    run=uuid.uuid4().hex[:16];project='abap-portfolio-'+run;prefix='/portfolio-demo-'+run;marker=uuid.uuid4().hex
    need(prefix not in json.dumps(original),'demo_prefix_already_present')
    baseline=stable(rows,project)
    work=Path('/run')/project;need(not work.exists() and not work.is_symlink(),'disposable_workspace_exists')
    work.mkdir(mode=0o700);identity=(work.stat().st_dev,work.stat().st_ino)
    report={'operation':'approved-public-linked-demonstration-20261104-1','status':'running','stage':'create_disposable_stack',
        'b2_requests':0,'ai_requests':0,'production_database_writes':False,'existing_n8n_workflows_modified':False,
        'production_web_recreated':False,'run':run,'project':project,'temporary_prefix':prefix,
        'baseline_origin_tls_smoke':baseline_origin,'authenticated_public_browser_required':True}
    save(report,True);proxy_changed=False;started=time.monotonic();configuration=None;proxy_restored=False
    def compose(*args,data=None,timeout=60):
        return docker('compose','--env-file','/dev/null','-p',project,'-f',str(work/'compose.json'),*args,data=data,timeout=timeout)
    try:
        (work/'.docker').mkdir(mode=0o700);DOCKER_CONFIG_PATH=str(work/'.docker')
        for name,data in payload.items():
            path=work/name;path.parent.mkdir(mode=0o755,parents=True,exist_ok=True);write_new(path,data,0o444)
        fixture.ROOT=work;configuration=fixture.fixture_configuration(work)
        db_alias=isolate_database(configuration,run)
        # Keep the disposable database namespace explicit and unique.
        configuration['services']['database']['cpus']=0.5
        configuration['services']['web']['cpus']=0.5
        configuration['services']['demo-provider']['cpus']=0.25
        configuration['services']['n8n']['cpus']=0.75
        configuration['services']['web']['environment'].update(PORTFOLIO_PREFIX=prefix,PORTFOLIO_VIEWER_MARKER=marker)
        old="uvicorn.run(create_web_application(session_secret=os.environ['ABAP_SESSION_SECRET'],secure_cookies=False),host='0.0.0.0',port=8000,access_log=False)"
        need(fixture.BOOT.count(old)==1,'fixture_bootstrap_admission_changed')
        boot=fixture.BOOT.replace(old,support.BOOT_TAIL).replace("'@database:'",repr('@'+db_alias+':'))
        (work/'bootstrap.py').write_text(boot);os.chmod(work/'bootstrap.py',0o444)
        os.chmod(work/'token',0o444) # Only a fresh dummy token; host parent stays root-private.
        write_new(work/'compose.json',json.dumps(configuration).encode())
        compose('up','-d','--no-build','--pull','never',timeout=90)
        report['stage']='wait_disposable_readiness';save(report);deadline=time.monotonic()+180
        while True:
            try:
                compose('exec','-T','web','python','-c',"import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8000/ready',timeout=2).status==200",timeout=10)
                compose('exec','-T','n8n','node','-e',"fetch('http://127.0.0.1:5678/healthz/readiness').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))",timeout=10)
                break
            except Stop:
                owned=[r for r in inventory() if r['Config'].get('Labels',{}).get('com.docker.compose.project')==project]
                need(not any(r['State']['Status']=='exited' and r['State']['ExitCode'] for r in owned),'disposable_service_exited')
                need(time.monotonic()<deadline,'disposable_readiness_timeout');time.sleep(2)
        report['stage']='linked_synthetic_acceptance';save(report)
        case=(fixture.CASE+support.COOKIE_TAIL).replace("'@database:'",repr('@'+db_alias+':'))
        raw=compose('exec','-T','web','python','-B','-',data=case.encode(),timeout=150)
        result=json.loads(raw.decode().splitlines()[-1]);need(result['status']=='PASS-linked-synthetic-local-demo','linked_synthetic_chain_failed')
        # Report location accurately: the same validated case now ran on the VPS.
        result['production_demo_executed']=True;result['scope']='disposable synthetic database on production VPS'
        report['linked_chain']=result
        cookie=compose('exec','-T','web','cat','/tmp/portfolio-service-cookie').decode();need(0<len(cookie)<8192,'private_fixture_cookie_unavailable')
        state=json.loads(compose('exec','-T','web','cat','/tmp/linked-state.json'))
        cid=compose('ps','-q','web').decode().strip();need(re.fullmatch('[a-f0-9]{64}',cid),'disposable_web_id_invalid')
        address=private_web_address(cid,project)
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with client.open('http://'+address+':8000/ready',timeout=5) as response:need(response.status==200,'host_caddy_cannot_reach_private_demo')
        snippet=support.proxy_snippet(auth,address+':8000',prefix,cookie,marker)
        adapted=json.loads(caddy_command('adapt','--config','/dev/stdin','--adapter','caddyfile',data=snippet.encode()))
        need(caddy_config()==original,'concurrent_proxy_change_before_load')
        temporary=support.temporary_config(original,adapted,prefix)
        report['stage']='temporary_authenticated_https_route';save(report);proxy_changed=True
        caddy_load(temporary)
        need(caddy_config()==temporary,'temporary_proxy_load_mismatch')
        urls={'customer':prefix+'/customers/'+state['customer'],'invoice':prefix+'/invoices/'+state['invoice'],'workflow':prefix+'/workflows/WF-PORTFOLIO'}
        status,_=origin_https(urls['invoice']);need(status in {302,303,401,403},'anonymous_demo_access_not_denied')
        report.update(stage='await_authenticated_browser',anonymous_origin_access_denied=True,
            public_urls={k:'https://app.dennisbasadre.com'+v for k,v in urls.items()});save(report)
        print(json.dumps({'event':'awaiting_authenticated_browser','public_urls':report['public_urls'],
            'instructions':'Keep this terminal open. Visit all three links while signed in to the existing ABAP account. Automatic cleanup follows verification or 10-minute timeout.'}),flush=True)
        deadline=time.monotonic()+600
        while True:
            p=docker('exec',cid,'python','-c',"import json,pathlib; p=pathlib.Path('/tmp/portfolio-browser-proof.json'); print(p.read_text() if p.exists() else '{}')")
            proof=json.loads(p)
            if proof=={'customer':200,'invoice':200,'workflow':200}:break
            need(time.monotonic()<deadline,'authenticated_browser_proof_timeout');time.sleep(2)
        report.update(status='PASS-public-linked-demonstration',stage='cleanup',authenticated_https_pages=proof)
        print(json.dumps({'event':'authenticated_https_pages_verified','cleanup_in_seconds':10}),flush=True)
        time.sleep(10)
    except BaseException as error:
        report.update(status='BLOCKED-public-linked-demonstration',failure={'stage':report['stage'],
            'code':str(error) if isinstance(error,Stop) else 'bounded_operation_error_suppressed',
            'diagnostic':LAST_DOCKER_FAILURE})
    finally:
        for name in ['SIGINT','SIGTERM','SIGHUP']:
            if hasattr(signal,name):signal.signal(getattr(signal,name),signal.SIG_IGN)
        errors=[]
        if proxy_changed:
            try:
                current=caddy_config()
                clean=original if current==original else remove_owned_route(current,prefix)
                if current!=clean:caddy_load(clean)
                need(caddy_config()==clean,'proxy_cleanup_verification_failed')
                report['original_proxy_configuration_restored']=clean==original
                proxy_restored=True
            except BaseException:errors.append('temporary_proxy_cleanup_blocked')
        else:proxy_restored=True
        if proxy_restored:
            try:
                ids=compose('ps','-aq').decode().split() if configuration else []
                if ids:
                    owned=json.loads(docker('inspect',*ids));need(all(r['Config']['Labels'].get('com.docker.compose.project')==project for r in owned),'cleanup_container_identity_changed')
                if configuration:compose('down','--volumes','--remove-orphans',timeout=90)
                need(not docker('ps','-aq','--filter','label=com.docker.compose.project='+project).strip(),'owned_containers_remain')
                need(work.resolve()==work and (work.stat().st_dev,work.stat().st_ino)==identity and work.stat().st_uid==0,'workspace_cleanup_identity_changed')
                shutil.rmtree(work);report['disposable_cleanup']='PASS'
            except BaseException:errors.append('owned_disposable_cleanup_blocked')
        try:
            report['production_state_preservation']='PASS' if stable(inventory(),project)==baseline else 'FAIL'
            report['host_proxy_process_preserved']=proxy_process()==pid
            report['final_origin_tls_smoke']=origin_smoke()
            need(report['production_state_preservation']=='PASS' and report['host_proxy_process_preserved']
                 and all(v==200 for v in report['final_origin_tls_smoke'].values()),'final_production_smoke_failed')
        except BaseException:errors.append('final_production_verification_blocked')
        if errors or report.get('original_proxy_configuration_restored') is False:report['status']='BLOCKED-final-cleanup-or-production-comparison'
        report['cleanup_errors']=errors;report['duration_seconds']=round(time.monotonic()-started,3);save(report)
    return report
if __name__=='__main__':
    def interrupted(*_):raise Stop('operator_interrupted')
    for name in ['SIGTERM','SIGHUP']:
        if hasattr(signal,name):signal.signal(getattr(signal,name),interrupted)
    try:result=main()
    except BaseException as error:result={'status':'BLOCKED-before-demonstration','code':str(error) if isinstance(error,Stop) else 'prerequisite_unavailable'}
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('PASS') else 1)
