"""New temporary HTTPS-demo guards only; no production/Docker/provider calls."""
import copy
import json
import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import portfolio_https_demo_support as support
m=runpy.run_path(str(ROOT/'deploy/hosthatch/run-public-linked-demonstration-once.py'))
PREFIX='/portfolio-demo-0123456789abcdef'

class PublicDemoTests(unittest.TestCase):
    def config(self):
        return {'apps':{'http':{'servers':{'live':{'routes':[{'match':[{'host':[support.HOST]}],
            'handle':[{'handler':'reverse_proxy','upstreams':[{'dial':'web:8000'}]}]}]}}}},'unrelated':{'keep':True}}
    def test_proxy_roundtrip_preserves_existing_configuration(self):
        original=self.config();adapted={'apps':{'http':{'servers':{'temporary':{'routes':[{'handle':[{'handler':'subroute','routes':[]}]}]}}}}}
        changed=support.temporary_config(original,adapted,PREFIX)
        self.assertEqual(m['remove_owned_route'](changed,PREFIX),original)
        self.assertEqual(len(original['apps']['http']['servers']['live']['routes']),1)
    def test_cleanup_preserves_concurrent_unrelated_change(self):
        original=self.config();adapted={'apps':{'http':{'servers':{'temporary':{'routes':[{'handle':[]} ]}}}}}
        changed=support.temporary_config(original,adapted,PREFIX);changed['unrelated']['added']='preserve'
        clean=m['remove_owned_route'](changed,PREFIX)
        self.assertEqual(clean['unrelated']['added'],'preserve')
        with self.assertRaises(m['Stop']):m['remove_owned_route'](original,PREFIX)
    def test_upstream_selection_and_injection_rejection(self):
        self.assertEqual(support.auth_dial(self.config()),'web:8000')
        with self.assertRaises(ValueError):support.proxy_snippet('web:8000\nmalicious','fixture:8000',PREFIX,'session=dummy','a'*32)
        with self.assertRaises(ValueError):support.proxy_snippet('web:8000','fixture:8000',PREFIX,'session="escape"','a'*32)
    def test_unique_fixture_database_cannot_resolve_production_alias(self):
        cfg={'services':{'database':{},'web':{'environment':{'DATABASE_URL':'postgresql://fixture:dummy@database:5432/abap_linked'}},
            'demo-provider':{'environment':{'DATABASE_URL':'postgresql://fixture:dummy@database:5432/abap_linked'}}}}
        alias=m['isolate_database'](cfg,'0'*16)
        for name in ['web','demo-provider']:
            self.assertIn('@'+alias+':',cfg['services'][name]['environment']['DATABASE_URL'])
            self.assertNotIn('@database:',cfg['services'][name]['environment']['DATABASE_URL'])
    def test_unapproved_mode_stops_before_access(self):
        with patch.object(os,'geteuid',return_value=0),patch.object(sys,'argv',['controller']):
            with self.assertRaisesRegex(m['Stop'],'explicit_authenticated_demo_approval_required'):m['main']()
    def test_failed_operation_diagnostic_excludes_arguments_and_stderr_values(self):
        process=types.SimpleNamespace(returncode=1,stdout=b'',stderr=b'Bearer SECRET_SENTINEL\nValueError: SECRET_SENTINEL\n')
        with patch.object(m['subprocess'],'run',return_value=process):
            with self.assertRaises(m['Stop']):m['docker']('compose','exec','SECRET_SENTINEL')
        diagnostic=m['docker'].__globals__['LAST_DOCKER_FAILURE']
        self.assertNotIn('SECRET_SENTINEL',str(diagnostic))
        self.assertEqual(diagnostic['error_classes'],['ValueError'])
    def test_origin_tls_uses_default_trust_hostname_and_does_not_follow_redirect(self):
        raw=Mock();context=Mock();connection=Mock()
        connection.getresponse.return_value.status=303
        connection.getresponse.return_value.read.return_value=b''
        with patch.object(m['ssl'],'create_default_context',return_value=context) as trust, \
             patch.object(m['ssl'],'_create_unverified_context',side_effect=AssertionError('TLS bypass forbidden')), \
             patch.object(m['socket'],'create_connection',return_value=raw) as connect, \
             patch.object(m['http'].client,'HTTPSConnection',return_value=connection):
            self.assertEqual(m['origin_https']('/protected'),(303,b''))
        trust.assert_called_once_with()
        connect.assert_called_once_with(('127.0.0.1',443),timeout=15)
        context.wrap_socket.assert_called_once_with(raw,server_hostname='app.dennisbasadre.com')
        connection.request.assert_called_once_with('GET','/protected',headers={'Host':'app.dennisbasadre.com'})
        connection.close.assert_called_once();raw.close.assert_called_once()
    def test_origin_certificate_failure_cannot_be_ignored(self):
        raw=Mock();context=Mock();connection=Mock()
        context.wrap_socket.side_effect=m['ssl'].SSLCertVerificationError('synthetic invalid certificate')
        with patch.object(m['ssl'],'create_default_context',return_value=context), \
             patch.object(m['socket'],'create_connection',return_value=raw), \
             patch.object(m['http'].client,'HTTPSConnection',return_value=connection):
            with self.assertRaisesRegex(m['Stop'],'origin_tls_certificate_verification_failed'):m['origin_https']('/health')
        connection.request.assert_not_called();raw.close.assert_called_once()
    def test_origin_smoke_failure_identifies_exact_endpoint(self):
        statuses={'/health':200,'/ready':503,'/login':200}
        with patch.dict(m['origin_smoke'].__globals__,origin_https=lambda path:(statuses[path],b'')):
            with self.assertRaisesRegex(m['Stop'],'origin_ready_status_503'):m['origin_smoke']()
    def network_fixture(self):
        return {'Config':{'Labels':{'com.docker.compose.project':'owned'}},'HostConfig':{'PortBindings':{}},
                'NetworkSettings':{'Networks':{'owned_default':{'IPAddress':'172.22.0.2'}}}}
    def test_private_network_address_guard(self):
        info=self.network_fixture();network={'Internal':True,'Labels':{'com.docker.compose.project':'owned'}}
        with patch.dict(m['private_web_address'].__globals__,docker=lambda *a:json.dumps([info if a[0]=='inspect' else network]).encode()):
            self.assertEqual(m['private_web_address']('id','owned'),'172.22.0.2')
    def test_public_binding_and_foreign_network_rejected(self):
        for problem in ['ports','foreign','external']:
            info=self.network_fixture();network={'Internal':True,'Labels':{'com.docker.compose.project':'owned'}}
            if problem=='ports':info['HostConfig']['PortBindings']={'8000/tcp':[{'HostIp':'0.0.0.0'}]}
            if problem=='foreign':network['Labels']['com.docker.compose.project']='other'
            if problem=='external':network['Internal']=False
            with self.subTest(problem=problem),patch.dict(m['private_web_address'].__globals__,docker=lambda *a:json.dumps([info if a[0]=='inspect' else network]).encode()):
                with self.assertRaises(m['Stop']):m['private_web_address']('id','owned')
    def test_prefixed_html_urls_only_for_gateway_marked_requests(self):
        from fastapi import FastAPI,Request
        from fastapi.testclient import TestClient
        app=FastAPI()
        @app.get('/invoices/{invoice_id}',name='invoice')
        def invoice(invoice_id:str):return {'id':invoice_id}
        @app.get('/customers/id')
        def customer(request:Request):return {'link':str(request.url_for('invoice',invoice_id='id'))}
        captured=[]
        namespace={'os':os,'create_web_application':lambda **kwargs:app,'uvicorn':types.SimpleNamespace(run=lambda application,**kwargs:captured.append(application))}
        with patch.dict(os.environ,ABAP_SESSION_SECRET='synthetic-only-secret',PORTFOLIO_VIEWER_MARKER='a'*32,PORTFOLIO_PREFIX=PREFIX):
            exec(support.BOOT_TAIL,namespace)
            client=TestClient(captured[0],base_url='https://app.dennisbasadre.com')
            self.assertEqual(client.get('/customers/id').json()['link'],'https://app.dennisbasadre.com/invoices/id')
            self.assertEqual(client.get('/customers/id',headers={'X-ABAP-Portfolio-Viewer':'a'*32}).json()['link'],
                'https://app.dennisbasadre.com'+PREFIX+'/invoices/id')
if __name__=='__main__':unittest.main()
