import hashlib
import json
import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from tests.test_advanced_assistant import AssistantFixture
from assistant_cloud_config import AssistantLimitError
from assistant_cloud_validate import free_openrouter
from assistant_gateway import configured_models, Gateway


class TestCloudRegistry(unittest.TestCase):
    def test_probe_verifies_text_protocol_without_claiming_native_tools(self):
        from assistant_cloud_validate import validate
        from assistant_gateway import Model
        with patch('assistant_gateway.Gateway.generate', side_effect=[('CLOUD_OK',{}),('確認しました。',{}),('{"tool":"leads"}',{})]):
            result=validate(Model('free','openrouter','vendor/free:free','synthetic'),
                            {'free_eligible':True,'native_tools_advertised':True})
        self.assertTrue(result['business_protocol_verified'])
        self.assertTrue(result['english_verified'])
        self.assertTrue(result['japanese_verified'])
        self.assertFalse(result['native_tools_verified'])

    def test_no_local_production_dependency_or_paid_openrouter(self):
        self.assertEqual(configured_models({'ABAP_ENVIRONMENT':'production',
            'ABAP_EXTERNAL_PROVIDER':'llama_cpp','ABAP_INTEGRATIONS_ENABLED':'true',
            'ABAP_ASSISTANT_ALLOW_LOCAL_DEVELOPMENT':'true'}), [])
        with self.assertRaises(ValueError):
            configured_models({'ABAP_ASSISTANT_OPENROUTER_MODELS':'vendor/paid'})

    def test_catalog_rejects_paid_and_nonzero_pricing(self):
        rows={'data':[{'id':'vendor/free:free','pricing':{'prompt':'0','completion':'0'},
            'supported_parameters':['tools']},
            {'id':'vendor/paid','pricing':{'prompt':'0','completion':'0'}},
            {'id':'vendor/paid:free','pricing':{'prompt':'0.01','completion':'0'}}]}
        result=free_openrouter(rows)
        self.assertEqual([r['model'] for r in result],['vendor/free:free'])
        self.assertTrue(result[0]['native_tools_advertised'])

    def test_stale_unverified_and_rotated_credentials_are_unavailable(self):
        identity='openrouter:vendor/free:free'
        env={'ABAP_ASSISTANT_OPENROUTER_MODELS':'vendor/free:free',
             'ABAP_ASSISTANT_OPENROUTER_KEY':'synthetic', 'ABAP_ASSISTANT_REMOTE_APPROVED':'true'}
        row={'id':identity,'checked_at':time.time(),'free_eligible':True,
            'access_verified':True,'business_protocol_verified':True,
            'key_fingerprint':hashlib.sha256(b'synthetic').hexdigest()}
        for change,expected in [({},True),({'checked_at':time.time()-90000},False),
            ({'free_eligible':False},False),({'business_protocol_verified':False},False),
            ({'key_fingerprint':'wrong'},False)]:
            with patch('assistant_cloud_config.evidence',return_value={identity:{**row,**change}}):
                model=configured_models(env)[0]
                self.assertEqual(model.available,expected)
                if not expected:
                    with self.assertRaises(ValueError):
                        Gateway([model]).select(identity)

    def test_gemini_requires_reviewed_free_account(self):
        identity='gemini:reviewed-free-model'
        row={'checked_at':time.time(),'free_eligible':True,'access_verified':True,
             'business_protocol_verified':True,'key_fingerprint':hashlib.sha256(b'synthetic').hexdigest()}
        env={'ABAP_ASSISTANT_GEMINI_MODELS':'reviewed-free-model',
             'ABAP_ASSISTANT_GEMINI_KEY':'synthetic','ABAP_ASSISTANT_REMOTE_APPROVED':'true',
             'ABAP_ASSISTANT_GEMINI_FREE_MODELS':'reviewed-free-model'}
        with patch('assistant_cloud_config.evidence',return_value={identity:row}):
            self.assertFalse(configured_models(env)[0].available)
            env['ABAP_ASSISTANT_GEMINI_FREE_ACCOUNT_REVIEWED']='true'
            self.assertTrue(configured_models(env)[0].available)

    def test_openrouter_sends_zero_price_and_disables_fallback(self):
        from assistant_gateway import Model
        calls=[]
        def transport(url,headers,body):
            calls.append(body)
            return {'choices':[{'message':{'content':'Synthetic response'}}]}
        gateway=Gateway([Model('free','openrouter','vendor/free:free','synthetic',available=True)],transport)
        gateway.generate('free','system','question')
        self.assertEqual(calls[0]['provider']['max_price'],{'prompt':0,'completion':0})
        self.assertFalse(calls[0]['provider']['allow_fallbacks'])
        self.assertNotIn('models',calls[0])

    def test_unexpected_reported_cost_fails_closed(self):
        from assistant_gateway import Model
        from agent_provider import AgentProviderError, AgentProviderFailureCode
        gateway=Gateway([Model('free','openrouter','vendor/free:free','synthetic',available=True)],
            lambda *args: {'choices':[{'message':{'content':'response'}}], 'usage':{'cost':0.01}})
        with self.assertRaises(AgentProviderError) as caught:
            gateway.generate('free','system','question')
        self.assertEqual(caught.exception.code,AgentProviderFailureCode.REQUEST_REJECTED)


class TestCloudLimits(AssistantFixture):
    def test_shared_provider_budget_and_atomic_reservation(self):
        with patch.dict(os.environ,{'ABAP_ASSISTANT_PROVIDER_DAILY_LIMIT':'1'}):
            lease=self.store.acquire_cloud(self.actor,'one','gemini')
            self.store.release_cloud(lease)
            with self.assertRaises(AssistantLimitError):
                self.store.acquire_cloud(self.other,'two','gemini')
            self.assertEqual(self.store.usage_summary(self.other)['model_calls'],0)
            lease=self.store.acquire_cloud(self.other,'two','openrouter')
            self.store.release_cloud(lease)

    def test_per_model_budget_across_users(self):
        with patch.dict(os.environ,{'ABAP_ASSISTANT_MODEL_DAILY_LIMIT':'1'}):
            lease=self.store.acquire_cloud(self.actor,'one','gemini')
            self.store.release_cloud(lease)
            with self.assertRaises(AssistantLimitError):
                self.store.acquire_cloud(self.other,'one','gemini')
            lease=self.store.acquire_cloud(self.other,'two','gemini')
            self.store.release_cloud(lease)

    def test_concurrency_limits_are_shared_and_release(self):
        with patch.dict(os.environ,{'ABAP_ASSISTANT_GLOBAL_CONCURRENCY':'1'}):
            def acquire(actor):
                try:
                    return self.store.acquire_cloud(actor,'one','gemini')
                except AssistantLimitError:
                    return None
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(acquire,[self.actor,self.other]))
            leases=[lease for lease in results if lease]
            self.assertEqual(len(leases),1)
            self.store.release_cloud(leases[0])
            self.store.release_cloud(self.store.acquire_cloud(self.other,'two','gemini'))

    def test_provider_cooldown_does_not_block_other_provider(self):
        self.store.mark_unavailable('one','gemini',provider_wide=True)
        with self.assertRaises(AssistantLimitError):
            self.store.acquire_cloud(self.other,'two','gemini')
        self.assertEqual(self.store.usage_summary(self.other)['model_calls'],0)
        self.store.release_cloud(self.store.acquire_cloud(self.other,'two','openrouter'))

    def test_minute_budget_is_distinct_from_daily(self):
        with patch.dict(os.environ,{'ABAP_ASSISTANT_PROVIDER_PER_MINUTE':'1'}):
            lease=self.store.acquire_cloud(self.actor,'one','gemini')
            self.store.release_cloud(lease)
            with self.assertRaises(AssistantLimitError):
                self.store.acquire_cloud(self.other,'two','gemini')

    def test_expired_lease_is_reclaimed(self):
        lease=self.store.acquire_cloud(self.actor,'one','gemini')
        connection=self.store._connect()
        connection.execute('UPDATE assistant_cloud_leases SET expires_at=0 WHERE lease_id=?',(lease,))
        connection.commit()
        connection.close()
        self.store.release_cloud(self.store.acquire_cloud(self.actor,'one','gemini'))
