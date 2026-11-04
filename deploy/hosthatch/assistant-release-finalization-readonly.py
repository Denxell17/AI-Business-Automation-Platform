#!/usr/bin/env python3
"""Read-only local VPS evidence. No repository clients, recovery or service writes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

PROJECT='abap-deploy'
COMPOSE=Path('/opt/abap-public-rag-production/releases/0ef5085524b6-r2/compose.deploy.yaml')
ENV_FILE='/etc/abap/production.env'
IMAGE='sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9'
DB_IMAGE='sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280'
BASE=Path('/var/backups/abap')
INPUT_SHA='f98ae09a197ef43f722f3cc8d07c1221ba06b8daf9701491906a17e86b448ce4'
EXPECTED={'application-image.tar':('36ee387eb1c96d3032586a05cab800081308e4003f6a369c197d386f08cca179',128000000),
 'application-configuration.tar':('2281312dbb691abe693dfb2467361e951624c840654c126bbe64958c76e5d0d8',2000000),
 'database.dump':('25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761',64000000)}
ENV={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/nonexistent','LC_ALL':'C'}
class Blocked(Exception):pass
def require(value):
    if not value:raise Blocked()
def sha(data):return hashlib.sha256(data).hexdigest()
def run(args,data=None):
    p=subprocess.run(args,input=data,capture_output=True,timeout=45,env=ENV)
    require(p.returncode==0 and len(p.stdout)<=4000000);return p.stdout
def docker(*args,data=None):
    require(args and (args[0] in ['ps','inspect'] or args[:2]==('image','inspect')
        or args[0]=='compose' and 'config' in args and not any(a in args for a in ['up','run','start','stop','restart','down','build','pull'])
        or args[:2]==('exec','-i') and len(args)==8 and args[3:7]==('python','-I','-B','-c')))
    return run(['/usr/bin/docker','--host','unix:///var/run/docker.sock',*args],data)
def envmap(rows):return dict(row.split('=',1) for row in rows or [] if '=' in row)
def backup_log_categories(raw):
    events=[]
    for line in raw.decode('utf-8','replace').splitlines():
        try:
            row=json.loads(line);text=str(row.get('MESSAGE','')).lower()
            category='backup_ok' if 'backup_ok:' in text else 'service_success' if 'deactivated successfully' in text or 'finished ' in text else 'service_failure' if 'failed' in text else None
            if category:events.append({'time_unix_microseconds':row.get('__REALTIME_TIMESTAMP'),'category':category})
        except (ValueError,TypeError):pass
    return events[-20:]
def inventory():
    ids=docker('ps','-aq','--filter','label=com.docker.compose.project='+PROJECT).decode().splitlines();require(ids)
    rows=json.loads(docker('inspect',*ids));return rows,sha(json.dumps([{k:r.get(k) for k in ['Id','Image','Config','HostConfig','Mounts','RestartCount']} for r in sorted(rows,key=lambda r:r['Id'])],sort_keys=True).encode())
def service(rows,name):
    found=[r for r in rows if (r['Config'].get('Labels') or {}).get('com.docker.compose.service')==name and r['State']['Running']]
    require(len(found)==1);return found[0]
def cached_artifacts(base=BASE):
    """Bounded, non-following scan of the known ABAP artifact directory only."""
    require(base.resolve()==base and base.is_dir() and base.stat().st_uid==0)
    queue=[(base,0)];checked=0;dirs=0;found=[];complete=True
    while queue:
        directory,depth=queue.pop();dirs+=1
        if dirs>100:complete=False;break
        with os.scandir(directory) as entries:
            for entry in entries:
                checked+=1
                if checked>2000:complete=False;break
                if entry.is_symlink():continue
                p=Path(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    if depth<3:queue.append((p,depth+1))
                    continue
                if entry.name not in EXPECTED or not entry.is_file(follow_symlinks=False):continue
                s=entry.stat(follow_symlinks=False);expected,limit=EXPECTED[entry.name]
                if s.st_uid!=0 or s.st_size>limit:continue
                h=hashlib.sha256()
                with p.open('rb') as f:
                    while True:
                        chunk=f.read(1048576)
                        if not chunk:break
                        h.update(chunk)
                found.append({'path':str(p),'bytes':s.st_size,'exact_preserved_hash_matches':h.hexdigest()==expected,'mode':oct(stat.S_IMODE(s.st_mode))})
                if len(found)>=20:complete=False;break
        if not complete:break
    return {'checked_scope':str(base),'maximum_depth':3,'scan_complete_within_limits':complete,'candidates':found,
        'missing_verified_artifacts':[n for n in EXPECTED if not any(Path(r['path']).name==n and r['exact_preserved_hash_matches'] for r in found)]}
def compare_runtime(web,image,resolved):
    view=resolved['services']['web'];labels=web['Config'].get('Labels') or {}
    expected={**envmap(image['Config'].get('Env')),**{k:str(v) for k,v in view.get('environment',{}).items()}}
    return {'image_matches':web['Image']==IMAGE,'database_image_expected':DB_IMAGE,
        'ordered_compose_matches':labels.get('com.docker.compose.project.config_files')==str(COMPOSE),
        'environment_file_matches':labels.get('com.docker.compose.project.environment_file')==ENV_FILE,
        'configured_image_matches':view.get('image')==web['Config'].get('Image'),
        'command_matches':view.get('command')==web['Config'].get('Cmd'),
        'entrypoint_matches':view.get('entrypoint',image['Config'].get('Entrypoint'))==web['Config'].get('Entrypoint'),
        'all_runtime_environment_matches':expected==envmap(web['Config'].get('Env'))}
def main():
    result={'scope':'read-only; zero repository/provider requests; no recovery or service writes','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    before=None
    try:
        unit=run(['/usr/bin/systemctl','show','abap-backup.service','-p','Result','-p','ExecMainStatus','-p','ExecMainStartTimestamp','-p','ExecMainExitTimestamp','--no-pager']).decode().splitlines()
        result['scheduled_backup_service']=dict(line.split('=',1) for line in unit if '=' in line)
        result['scheduled_backup_log_events']=backup_log_categories(run(['/usr/bin/journalctl','-u','abap-backup.service','--since','2026-11-03','--no-pager','-o','json','-n','30']))
    except Exception:result['scheduled_backup_logs']='BLOCKED-readonly-service-evidence'
    try:result['local_artifacts']=cached_artifacts()
    except Exception:result['local_artifacts']={'status':'BLOCKED-protected-artifact-metadata'}
    try:
        rows,before=inventory();web=service(rows,'web');db=service(rows,'database');require(db['Image']==DB_IMAGE)
        image=json.loads(docker('image','inspect',IMAGE))[0]
        result['cached_exact_production_image']=image['Id']==IMAGE
        args=['compose','--project-directory',str(COMPOSE.parent),'--env-file',ENV_FILE,'-p',PROJECT,'-f',str(COMPOSE)]
        resolved=json.loads(docker(*args,'config','--format','json'))
        result['production_configuration']=compare_runtime(web,image,resolved)
        raw=(Path(__file__).resolve().parent/'review-inputs.json').read_bytes();require(len(raw)<131072 and sha(raw)==INPUT_SHA);bundle=json.loads(raw)
        require(sha(COMPOSE.read_bytes())==bundle['production_compose_sha256'])
        proposed=json.loads(docker(*args,'-f','-','config','--format','json',data=json.dumps(bundle['disabled_overlay']).encode()))
        old=resolved['services']['web'];new=proposed['services']['web'];env=new.get('environment',{})
        nonassistant=lambda e:{k:v for k,v in e.items() if not k.startswith('ABAP_ASSISTANT_') and k not in ['ABAP_ADVANCED_ASSISTANT_ENABLED','ABAP_ENVIRONMENT']}
        result['disabled_proposal']={'other_services_unchanged':all(v==proposed['services'].get(k) for k,v in resolved['services'].items() if k!='web'),
            'nonassistant_environment_unchanged':nonassistant(old.get('environment',{}))==nonassistant(env),
            'existing_volumes_preserved':all(v in new.get('volumes',[]) for v in old.get('volumes',[])),
            'networks_and_existing_secrets_preserved':all(old.get(k)==new.get(k) for k in ['networks','secrets','ports','command','depends_on']),
            'default_off':env.get('ABAP_ADVANCED_ASSISTANT_ENABLED')=='false' and env.get('ABAP_ASSISTANT_REMOTE_APPROVED')=='false',
            'synthetic_only':env.get('ABAP_ASSISTANT_DEMO_ONLY')=='true','assistant_workflows_empty':env.get('ABAP_ASSISTANT_N8N_WORKFLOWS')=='',
            'candidate_image_matches':new['image']==bundle['candidate_tag']}
        sources=bundle['candidate_source_hashes']
        require(len(sources)<=200 and all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in sources))
        # Read fixed application code only; no environment, data, logs or documents.
        program="import hashlib,json,pathlib,sys; names=json.load(sys.stdin); print(json.dumps({n:hashlib.sha256((pathlib.Path('/app')/n).read_bytes()).hexdigest() if (pathlib.Path('/app')/n).is_file() else None for n in names}))"
        actual=json.loads(docker('exec','-i',web['Id'],'python','-I','-B','-c',program,data=json.dumps(list(sources)).encode()))
        critical=[n for n in sources if Path(n).name.startswith('public_rag_') or Path(n).name=='public-rag-chat.js']
        result['application_source_comparison']={'matching_files':sum(actual.get(n)==h for n,h in sources.items()),
            'different_existing_files':[n for n,h in sources.items() if actual.get(n) is not None and actual[n]!=h],
            'candidate_only_files':[n for n in sources if actual.get(n) is None],
            'public_rag_specific_files_unchanged':all(actual.get(n)==sources[n] for n in critical),'public_rag_specific_files_checked':len(critical)}
    except Exception:result['protected_configuration_check']='BLOCKED-readonly-check-or-review-inputs-unavailable'
    finally:
        if before is not None:
            try:result['production_state_preservation']={'status':'PASS' if inventory()[1]==before else 'FAIL'}
            except Exception:result['production_state_preservation']={'status':'BLOCKED'}
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
