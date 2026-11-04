import os
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from tests.test_advanced_assistant import AssistantFixture, FakeGateway
from assistant_demo import QUESTIONS, ACTION_QUESTIONS, ACTION, visible_entries, demo_only
from assistant_tools import read_tool, validate_action
from advanced_assistant import converse
from assistant_confirmation import confirm_action
from database import get_database_connection


class DemoFixture(AssistantFixture):
    def setUp(self):
        super().setUp()
        self.mode=patch.dict(os.environ,{'ABAP_ASSISTANT_DEMO_ONLY':'true'})
        self.mode.start()
        self.addCleanup(self.mode.stop)

class TestSyntheticBoundary(DemoFixture):
    def test_arbitrary_private_input_rejected_before_provider(self):
        gateway=FakeGateway()
        for question in ['Private customer name and invoice secret', QUESTIONS[0]+' extra', 'https://private.example']:
            with self.assertRaises(PermissionError):
                converse(self.actor,question,'test','en',True,self.db,self.store,gateway)
        self.assertEqual(gateway.calls,[])

    def test_all_reads_use_fixtures_not_live_repository(self):
        with patch('assistant_tools._query',side_effect=AssertionError('Live repository queried')):
            for tool in ['leads','customers','invoices','employees','workflows','activity']:
                result=read_tool(self.actor,{'tool':tool},self.db)
                self.assertIn('SYNTHETIC',result['scope'])
                self.assertNotIn('Owned',str(result))
                self.assertNotIn('PrivateOther',str(result))

    def test_demo_does_not_grant_viewer_tool_permissions(self):
        with self.assertRaises(PermissionError):
            read_tool(self.viewer,{'tool':'leads'},self.db)

    def test_provider_receives_only_fixed_prompt_and_synthetic_result(self):
        gateway=FakeGateway(['{"tool":"leads"}','Synthetic result'])
        converse(self.actor,QUESTIONS[1],'test','en',True,self.db,self.store,gateway)
        self.assertEqual(gateway.calls[0][2],QUESTIONS[1])
        self.assertIn('Synthetic Lead Alpha',gateway.calls[1][2])
        self.assertNotIn(self.actor['username'],gateway.calls[1][2])
        self.assertNotIn('Owned',gateway.calls[1][2])

    def test_browser_summary_without_share_checkbox_permits_only_fixed_fixture(self):
        for question,tool,language in [(QUESTIONS[1],'leads','en'),(QUESTIONS[6],'invoices','ja')]:
            gateway=FakeGateway(['{"tool":"'+tool+'"}','Synthetic fixture summary'])
            converse(self.actor,question,'test',language,False,self.db,self.store,gateway)
            self.assertNotIn('Business data access is disabled',gateway.calls[0][1])
            self.assertIn('Return ONLY this JSON',gateway.calls[0][1])
            self.assertIn('"tool": "'+tool+'"',gateway.calls[0][1])
            self.assertIn('SYNTHETIC DEMONSTRATION ONLY',gateway.calls[1][2])
            self.assertNotIn(self.actor['username'],gateway.calls[1][2])

    def test_model_write_or_extra_arguments_never_reach_business_services(self):
        for answer in ['{"tool":"create_lead","name":"Untrusted"}', '{"tool":"leads","query":"secret"}']:
            with self.assertRaises((ValueError,PermissionError)):
                converse(self.actor,QUESTIONS[1],'test','en',True,self.db,self.store,FakeGateway([answer]))
        with self.assertRaises(PermissionError):
            validate_action(self.actor,{'tool':'start_workflow','workflow_id':'REAL'},self.db)

    def propose(self):
        return converse(self.actor,ACTION_QUESTIONS[0],'test','en',False,self.db,self.store,FakeGateway())

    def test_confirm_creates_only_isolated_demo_record(self):
        identity=self.propose()
        with self.assertRaises(ValueError):
            confirm_action(self.store,self.other,identity)
        result=confirm_action(self.store,self.actor,identity)
        self.assertTrue(result.startswith('DEMO-'))
        with self.assertRaises(ValueError):
            confirm_action(self.store,self.actor,identity)
        connection=get_database_connection(self.db)
        self.assertEqual(connection.execute('SELECT COUNT(*) FROM leads').fetchone()[0],2)
        self.assertEqual(connection.execute('SELECT COUNT(*) FROM assistant_demo_leads').fetchone()[0],1)
        connection.close()
        self.assertIn(result,str(read_tool(self.actor,{'tool':'leads'},self.db)))
        self.assertNotIn(result,str(read_tool(self.other,{'tool':'leads'},self.db)))

    def test_old_business_proposal_and_mode_switch_fail_closed(self):
        old=self.store.add(self.actor,'action',{'arguments':ACTION,'review':{}})
        with self.assertRaises(PermissionError):
            confirm_action(self.store,self.actor,old)
        identity=self.propose()
        with patch.dict(os.environ,{'ABAP_ASSISTANT_DEMO_ONLY':'false'}):
            with self.assertRaises(PermissionError):
                confirm_action(self.store,self.actor,identity)

    def test_confirmation_rollback_and_concurrency(self):
        identity=self.propose()
        with patch.object(self.store,'add',side_effect=ValueError('Injected failure')):
            with self.assertRaises(ValueError):
                confirm_action(self.store,self.actor,identity)
        def confirm(_):
            try:return confirm_action(self.store,self.actor,identity)
            except ValueError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(bool(x) for x in pool.map(confirm,range(2))),1)

    def test_demo_history_clear_preserves_old_private_history(self):
        self.store.add(self.actor,'chat',{'answer':'PRIVATE_HISTORY'})
        self.store.add(self.actor,'chat',{'answer':'Synthetic','demo_only':True})
        visible=visible_entries(self.store.entries(self.actor))
        self.assertEqual(len(visible),1)
        self.store.clear(self.actor,demo=True)
        self.assertIn('PRIVATE_HISTORY',str(self.store.entries(self.actor)))
        self.assertEqual(visible_entries(self.store.entries(self.actor)),[])


class TestProductionDemoDefault(unittest.TestCase):
    def test_production_defaults_to_restricted_mode(self):
        with patch.dict(os.environ,{'ABAP_ENVIRONMENT':'production'}):
            os.environ.pop('ABAP_ASSISTANT_DEMO_ONLY',None)
            self.assertTrue(demo_only())


class TestDemoBrowser(DemoFixture):

    def test_demo_browser_controls_and_tampered_posts(self):
        from fastapi.testclient import TestClient
        from web_app import create_web_application
        from tests.web_auth import sign_in, csrf_token_from_page
        gateway=FakeGateway()
        self.store.add(self.actor,'chat',{'question':'PRIVATE_HISTORY','answer':'Confidential'})
        with patch.dict(os.environ,{'ABAP_ADVANCED_ASSISTANT_ENABLED':'true'}), \
             patch('assistant_gateway.configured_models',return_value=gateway.models), \
             patch('assistant_gateway.Gateway.generate',side_effect=gateway.generate):
            with TestClient(create_web_application(database_file=self.db,session_secret='synthetic-browser-session')) as client:
                self.assertEqual(client.get('/ai-assistant/advanced',follow_redirects=False).status_code,303)
                sign_in(client,'Owner','StrongTestPassword123!')
                response=client.get('/ai-assistant/advanced')
                self.assertEqual(response.status_code,200)
                self.assertIn('Synthetic demonstration only',response.text)
                self.assertNotIn('PRIVATE_HISTORY',response.text)
                self.assertNotIn('<textarea',response.text)
                self.assertNotIn('name="share_data"',response.text)
                token=csrf_token_from_page(client,'/ai-assistant/advanced')
                response=client.post('/ai-assistant/advanced',data={'csrf_token':token,
                    'question':'Private arbitrary input','model_id':'test','share_data':'yes','demo_only':'false'})
                self.assertEqual(response.status_code,403)
                self.assertEqual(gateway.calls,[])
                response=client.post('/ai-assistant/advanced',data={'csrf_token':token,
                    'question':ACTION_QUESTIONS[0],'model_id':'test'})
                self.assertEqual(response.status_code,200)
                self.assertIn('Confirm this exact action',response.text)
                identity=next(r['entry_id'] for r in self.store.entries(self.actor,demo=True) if r['kind']=='action')
                path='/ai-assistant/advanced/actions/'+identity
                self.assertEqual(client.post(path,data={'csrf_token':'wrong','decision':'confirm'}).status_code,403)
                self.assertEqual(client.post(path,data={'csrf_token':token,'decision':'confirm'}).status_code,200)
                self.assertEqual(client.post(path,data={'csrf_token':token,'decision':'confirm'}).status_code,409)
                private=self.store.add(self.actor,'action',{'arguments':ACTION,'review':{}})
                self.assertEqual(client.post('/ai-assistant/advanced/actions/'+private,
                    data={'csrf_token':token,'decision':'cancel'}).status_code,409)
                self.assertEqual(next(r['state'] for r in self.store.entries(self.actor) if r['entry_id']==private),'pending')
