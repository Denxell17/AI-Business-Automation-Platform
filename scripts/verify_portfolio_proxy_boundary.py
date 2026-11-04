"""Focused new HTTPS-route boundary check; cached local images, network none."""
import json
from pathlib import Path
import subprocess
import tempfile
import time
import uuid
from portfolio_https_demo_support import proxy_snippet,temporary_config,HOST

APP='sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c'
CADDY='caddy:2.10.2-alpine'
SERVER=r'''
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import threading,json
class Auth(BaseHTTPRequestHandler):
 def do_GET(self):
  allowed=self.path=='/ai-assistant/advanced' and self.headers.get('Cookie')=='production_login=authorized'
  self.send_response(200 if allowed else 302)
  if not allowed:self.send_header('Location','/login')
  self.end_headers()
 def log_message(self,*a):pass
class Demo(BaseHTTPRequestHandler):
 def do_GET(self):
  assert self.headers.get('Cookie')=='session=synthetic_fixture'
  assert self.headers.get('X-ABAP-Portfolio-Viewer')=='a'*32
  self.send_response(200);self.send_header('Set-Cookie','fixture=must-not-reach-browser');self.end_headers()
  self.wfile.write(json.dumps({'path':self.path}).encode())
 def log_message(self,*a):pass
threading.Thread(target=ThreadingHTTPServer(('127.0.0.1',8000),Auth).serve_forever,daemon=True).start()
ThreadingHTTPServer(('127.0.0.1',8001),Demo).serve_forever()
'''
PROBE=r'''
import urllib.request,urllib.error,json
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a):return None
client=urllib.request.build_opener(NoRedirect())
def request(cookie=None):
 headers={'Host':'app.dennisbasadre.com'}
 if cookie:headers['Cookie']=cookie
 r=urllib.request.Request('http://127.0.0.1:8088/portfolio-demo-0123456789abcdef/invoices/fixture',headers=headers)
 try:return client.open(r,timeout=5)
 except urllib.error.HTTPError as e:return e
r=request();assert r.code==302,('anonymous_status',r.code)
r=request('session=synthetic_fixture');assert r.code==302,('forged_fixture_status',r.code)
r=request('production_login=authorized')
assert r.code==200,('authenticated_status',r.code)
assert json.load(r)['path']=='/invoices/fixture','prefix_not_stripped'
assert r.headers.get('Set-Cookie') is None
print(json.dumps({'anonymous_denied':True,'fixture_cookie_cannot_bypass_production_auth':True,'authenticated_prefix_and_delegation':True,'production_cookie_preserved':True}))
'''
def main():
    run=uuid.uuid4().hex[:12];names=['abap-proxy-case-'+run,'abap-proxy-gate-'+run]
    def docker(*args,data=None):
        p=subprocess.run(['docker','--context','desktop-linux',*args],input=data,capture_output=True,timeout=30)
        if p.returncode:
            text=p.stderr.decode('utf8','replace')[-1200:].replace('synthetic_fixture','[fixture]').replace('production_login=authorized','[fixture]')
            raise RuntimeError('local_proxy_operation_failed_'+str(p.returncode)+' '+text)
        return p.stdout+p.stderr if args[0]=='logs' else p.stdout
    with tempfile.TemporaryDirectory(prefix='abap-proxy-',dir=str(Path.home()/'Downloads')) as tmp:
        root=Path(tmp);(root/'server.py').write_text(SERVER)
        snippet=proxy_snippet('127.0.0.1:8000','127.0.0.1:8001','/portfolio-demo-0123456789abcdef','session=synthetic_fixture','a'*32)
        adapted=json.loads(docker('run','--rm','--pull','never','--network','none','--read-only','-i','--entrypoint','caddy',CADDY,'adapt','--config','/dev/stdin','--adapter','caddyfile',data=snippet.encode()))
        original={'apps':{'http':{'servers':{'fixture':{'listen':[':8088'],'automatic_https':{'disable':True},'routes':[
            {'match':[{'host':[HOST]}],'handle':[{'handler':'reverse_proxy','upstreams':[{'dial':'127.0.0.1:8000'}]}]}]}}}}}
        config=temporary_config(original,adapted,'/portfolio-demo-0123456789abcdef')
        assert len(original['apps']['http']['servers']['fixture']['routes'])==1
        (root/'config.json').write_text(json.dumps(config));owned=[]
        try:
            for name,image,args in [(names[0],APP,['--network','none','--user','10001:10001','--entrypoint','python']),
                                    (names[1],CADDY,['--network','container:'+names[0],'--cap-add','NET_BIND_SERVICE','--tmpfs','/config','--tmpfs','/data','--entrypoint','caddy'])]:
                cmd=['/fixture/server.py'] if name==names[0] else ['run','--config','/fixture/config.json']
                docker('run','-d','--pull','never','--name',name,'--label','com.abap.proxy-case='+run,'--read-only','--cap-drop','ALL',
                    '--security-opt','no-new-privileges','--mount','type=bind,source='+str(root)+',target=/fixture,readonly',*args,image,*cmd)
                owned.append(name)
            deadline=time.monotonic()+15
            while True:
                info=json.loads(docker('inspect',names[1]))[0]
                if not info['State']['Running']:raise RuntimeError('fixture_caddy_exited')
                try:result=json.loads(docker('exec','-i',names[0],'python','-B','-',data=PROBE.encode()));break
                except RuntimeError:
                    if time.monotonic()>deadline:raise
                    time.sleep(.5)
            print(json.dumps({'status':'PASS-temporary-proxy-auth-boundary','checks':result,'production_changes':False}))
        except BaseException:
            if names[1] in owned:
                text=docker('logs','--tail','12',names[1]).decode('utf8','replace')
                # Only dummy local credentials exist in this fixture.
                print(text.replace('synthetic_fixture','[fixture]').replace('a'*32,'[fixture-marker]')[-2400:])
            raise
        finally:
            for name in reversed(owned):
                info=json.loads(docker('inspect',name))[0]
                if info['Config']['Labels'].get('com.abap.proxy-case')!=run:raise RuntimeError('cleanup_identity_changed')
                docker('rm','-f',name)
if __name__=='__main__':main()
