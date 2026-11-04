import os
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from tests.test_advanced_assistant import AssistantFixture
from assistant_tools import validate_action, action_review, read_tool
from assistant_confirmation import confirm_action
from database import get_database_connection

class TestAtomicConfirmation(AssistantFixture):
    def proposal(self, values):
        values = validate_action(self.actor, values, self.db)
        return self.store.add(self.actor, 'action', {'arguments': values,
            'review': action_review(self.actor, values, self.db)})

    def test_rollback_restores_claim_and_business_records(self):
        identity = self.proposal({'tool':'create_lead','name':'Atomic rollback'})
        original = self.store.add
        def fail(*args, **kwargs):
            if args[1] == 'chat':
                raise ValueError('Injected result persistence failure')
            return original(*args, **kwargs)
        with patch.object(self.store, 'add', side_effect=fail):
            with self.assertRaises(ValueError):
                confirm_action(self.store,self.actor,identity)
        self.assertNotIn('Atomic rollback', str(read_tool(self.actor,{'tool':'leads'},self.db)))
        self.assertEqual(next(e for e in self.store.entries(self.actor) if e['entry_id']==identity)['state'],'pending')
        self.assertTrue(confirm_action(self.store,self.actor,identity))

    def test_concurrent_confirmations_commit_once(self):
        identity = self.proposal({'tool':'create_lead','name':'Once only'})
        def confirm(_):
            try:
                confirm_action(self.store,self.actor,identity)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(confirm,range(2))),1)
        self.assertEqual(sum(r['name']=='Once only' for r in read_tool(self.actor,{'tool':'leads'},self.db)['records']),1)

    def test_all_domain_writes_share_confirmation_transaction(self):
        from crm_service import update_lead
        identity=self.proposal({'tool':'update_lead','lead_id':self.owned,'name':'Atomic customer','stage':'contacted'})
        confirm_action(self.store,self.actor,identity)
        identity=self.proposal({'tool':'update_lead','lead_id':self.owned,'name':'Atomic customer','stage':'qualified'})
        confirm_action(self.store,self.actor,identity)
        customer=confirm_action(self.store,self.actor,self.proposal({'tool':'prepare_customer','lead_id':self.owned}))
        invoice=confirm_action(self.store,self.actor,self.proposal({'tool':'draft_invoice','customer_id':customer,
            'invoice_number':'ATOMIC-1','lines':[{'description':'Test','quantity':'1','unit_price':'10'}]}))
        self.assertTrue(invoice)

    def test_n8n_outbox_is_atomic_and_duplicate_safe(self):
        from workflow_service import create_workflow,create_workflow_task,update_workflow
        create_workflow(self.actor,'WF-ATOMIC','Atomic workflow','','draft',self.db)
        create_workflow_task(self.actor,'TASK-ATOMIC','WF-ATOMIC',1,'Test','','manual',True,self.db)
        update_workflow(self.actor,'WF-ATOMIC','Atomic workflow','','active',self.db,n8n_enabled=True)
        with patch.dict(os.environ,{'ABAP_ASSISTANT_N8N_WORKFLOWS':'WF-ATOMIC'}), patch('integration_config.load_integration_settings',return_value={'enabled':True}):
            identity=self.proposal({'tool':'start_workflow','workflow_id':'WF-ATOMIC'})
            with patch('webhook_delivery_service.queue_outbound_webhook_delivery',return_value=False):
                with self.assertRaises(ValueError):
                    confirm_action(self.store,self.actor,identity)
            c=get_database_connection(self.db)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM workflow_executions').fetchone()[0],0)
            c.close()
            execution=confirm_action(self.store,self.actor,identity)
            with self.assertRaises(ValueError):
                confirm_action(self.store,self.actor,identity)
            c=get_database_connection(self.db)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM webhook_deliveries WHERE correlation_id=?',(execution,)).fetchone()[0],1)
            c.close()

            from datetime import datetime, timezone
            from uuid import uuid4
            from webhook_contract import build_webhook_envelope
            from webhook_delivery_service import apply_verified_inbound_workflow_result
            now=datetime.now(timezone.utc)
            callback=build_webhook_envelope(str(uuid4()),execution,'workflow.execution.result',now,{'status':'completed'})
            self.assertTrue(apply_verified_inbound_workflow_result(callback,now,300,self.db)['applied'])
            self.assertTrue(apply_verified_inbound_workflow_result(callback,now,300,self.db)['duplicate'])


    def test_invoice_failure_rolls_back_line_items_and_claim(self):
        from crm_service import update_lead,convert_lead
        for stage in ('contacted','qualified'):
            update_lead(self.actor,self.owned,'Customer','','','',stage,self.actor['user_id'],self.db)
        customer=convert_lead(self.actor,self.owned,self.db)
        identity=self.proposal({'tool':'draft_invoice','customer_id':customer,
            'invoice_number':'ROLLBACK-1','lines':[{'description':'Test','quantity':'1','unit_price':'10'}]})
        with patch.object(self.store,'add',side_effect=ValueError('Injected failure')):
            with self.assertRaises(ValueError):
                confirm_action(self.store,self.actor,identity)
        c=get_database_connection(self.db)
        self.assertEqual(c.execute('SELECT COUNT(*) FROM invoices').fetchone()[0],0)
        self.assertEqual(c.execute('SELECT COUNT(*) FROM invoice_line_items').fetchone()[0],0)
        c.close()

    def test_revocation_and_stale_review_do_not_commit(self):
        from database import update_user_account_active_status
        from crm_service import update_lead
        identity=self.proposal({'tool':'update_lead','lead_id':self.owned,'name':'Proposed','stage':'contacted'})
        update_lead(self.actor,self.owned,'Changed','','','','new',self.actor['user_id'],self.db)
        with self.assertRaises(ValueError):
            confirm_action(self.store,self.actor,identity)
        identity=self.proposal({'tool':'create_lead','name':'Revoked'})
        update_user_account_active_status(self.actor['username'],False,self.db)
        with self.assertRaises(PermissionError):
            confirm_action(self.store,self.actor,identity)


@unittest.skipUnless(os.environ.get('ABAP_TEST_DATABASE_URL'), 'Isolated ABAP_TEST_DATABASE_URL required.')
class TestPostgresqlAtomic(TestAtomicConfirmation):
    def setUp(self):
        import psycopg
        from psycopg import sql
        from urllib.parse import quote
        from uuid import uuid4
        from postgresql_migrations import apply_postgresql_migrations
        self.test_url=os.environ['ABAP_TEST_DATABASE_URL']
        self.schema='assistant_test_'+uuid4().hex
        with psycopg.connect(self.test_url) as connection:
            connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
        scoped=self.test_url+('&' if '?' in self.test_url else '?')+'options='+quote('-c search_path='+self.schema)
        self.pg_environment=patch.dict(os.environ,{'DATABASE_BACKEND':'postgresql','DATABASE_URL':scoped})
        self.pg_environment.start()
        self.addCleanup(self.pg_environment.stop)
        def cleanup_schema():
            with psycopg.connect(self.test_url) as connection:
                connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(self.schema)))
        self.addCleanup(cleanup_schema)
        apply_postgresql_migrations(scoped)
        super().setUp()
