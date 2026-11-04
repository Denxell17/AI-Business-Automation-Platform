"""Temporary demonstration glue; never installed in the production application."""
import copy
import re

HOST='app.dennisbasadre.com'

def proxy_snippet(auth_upstream,demo_upstream,prefix,cookie,marker):
    if not all(re.fullmatch(r'[a-zA-Z0-9_.:-]+',v) for v in [auth_upstream,demo_upstream]):
        raise ValueError('untrusted_upstream')
    if not re.fullmatch(r'/portfolio-demo-[a-f0-9]{16}',prefix):raise ValueError('untrusted_prefix')
    if not re.fullmatch(r'[a-zA-Z0-9_=.;+:/ -]+',cookie) or not re.fullmatch(r'[a-f0-9]{32}',marker):raise ValueError('untrusted_fixture_credential')
    return (':8088 {\n route {\n forward_auth '+auth_upstream+' {\n uri /ai-assistant/advanced\n }\n'
        +' uri strip_prefix '+prefix+'\n reverse_proxy '+demo_upstream+' {\n'
        +' header_up Cookie "'+cookie+'"\n header_up X-ABAP-Portfolio-Viewer "'+marker+'"\n'
        +' header_down -Set-Cookie\n header_down Cache-Control "private, no-store"\n }\n }\n}\n')

def host_route(config):
    found=[]
    for name,server in config.get('apps',{}).get('http',{}).get('servers',{}).items():
        for index,route in enumerate(server.get('routes',[])):
            if any(HOST in group.get('host',[]) for group in route.get('match',[])):
                found.append((name,index,route))
    if len(found)!=1:raise ValueError('ambiguous_public_app_route')
    return found[0]

def auth_dial(config):
    _,_,route=host_route(config);found=[]
    def visit(value):
        if isinstance(value,dict):
            if value.get('handler')=='reverse_proxy':
                found.extend(v['dial'] for v in value.get('upstreams',[]) if 'dial' in v)
            for v in value.values():visit(v)
        elif isinstance(value,list):
            for v in value:visit(v)
    visit(route)
    if len(set(found))!=1:raise ValueError('ambiguous_existing_app_upstream')
    return found[0]

def temporary_config(original,adapted,prefix):
    result=copy.deepcopy(original);name,index,_=host_route(result)
    servers=adapted['apps']['http']['servers']
    if len(servers)!=1:raise ValueError('unexpected_adapted_proxy')
    routes=next(iter(servers.values()))['routes']
    if len(routes)!=1:raise ValueError('unexpected_adapted_routes')
    addition=copy.deepcopy(routes[0])
    addition['match']=[{'host':[HOST],'path':[prefix+'/*'],'method':['GET']}]
    result['apps']['http']['servers'][name]['routes'].insert(index,addition)
    check=copy.deepcopy(result);check['apps']['http']['servers'][name]['routes'].pop(index)
    if check!=original:raise ValueError('unrelated_proxy_change')
    return result

# Only gateway-authenticated requests get the prefix and contribute browser proof.
# The native demo account/session remains private between Caddy and this fixture.
BOOT_TAIL=r'''
application=create_web_application(session_secret=os.environ['ABAP_SESSION_SECRET'],secure_cookies=False)
class PortfolioApplication:
 async def __call__(self,scope,receive,send):
  if scope['type']!='http':return await application(scope,receive,send)
  marker=dict(scope.get('headers',[])).get(b'x-abap-portfolio-viewer',b'').decode()
  viewer=marker==os.environ['PORTFOLIO_VIEWER_MARKER']
  if viewer:
   scope=dict(scope);scope['root_path']=os.environ['PORTFOLIO_PREFIX']
  status=None
  async def capture(message):
   nonlocal status
   if message['type']=='http.response.start':status=message['status']
   await send(message)
  await application(scope,receive,capture)
  if viewer and status==200:
   import json
   state_path='/tmp/linked-state.json'
   try:
    with open(state_path) as f:state=json.load(f)
    expected={'/customers/'+state['customer']:'customer','/invoices/'+state['invoice']:'invoice','/workflows/WF-PORTFOLIO':'workflow'}
    if scope['path'] in expected:
     proof_path='/tmp/portfolio-browser-proof.json'
     try:
      with open(proof_path) as f:proof=json.load(f)
     except FileNotFoundError:proof={}
     proof[expected[scope['path']]]=status
     temporary=proof_path+'.new'
     with open(temporary,'w') as f:json.dump(proof,f)
     os.replace(temporary,proof_path)
   except (OSError,KeyError,ValueError):pass
uvicorn.run(PortfolioApplication(),host='0.0.0.0',port=8000,access_log=False,proxy_headers=True,forwarded_allow_ips='*')
'''

COOKIE_TAIL=r'''
import os
with open('/tmp/portfolio-service-cookie','x') as f:
 os.chmod(f.name,0o600)
 f.write('; '.join(cookie.name+'='+cookie.value for cookie in jar))
'''
