"""New renewal-only fixtures: no live requests or production operations."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path('/workspace')
class ValidationRenewalTests(unittest.TestCase):
    def setUp(self):
        p=ROOT/'deploy/hosthatch/renew-assistant-model-validation.py'
        s=importlib.util.spec_from_file_location('renewal_fixture',p);self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m)
        self.now=1800000000
        self.env={'ABAP_ADVANCED_ASSISTANT_ENABLED':'true','ABAP_ASSISTANT_REMOTE_APPROVED':'true',
            'ABAP_ASSISTANT_DEMO_ONLY':'true','ABAP_ASSISTANT_OPENROUTER_KEY':'fixture-key',
            'ABAP_ASSISTANT_OPENROUTER_MODELS':','.join(i.removeprefix('openrouter:') for i in self.m.APPROVED)}
        self.rows=[{'id':i,'provider':'openrouter','model':i.removeprefix('openrouter:'),'checked_at':self.now-70000,
            'key_fingerprint':hashlib.sha256(b'fixture-key').hexdigest(),'free_eligible':True,'access_verified':True,
            'business_protocol_verified':True,'english_verified':True,'japanese_verified':True,'native_tools_verified':False} for i in self.m.APPROVED]
        self.calls=[];self.probes=[]
    def fetch(self,host,path,headers=None):
        self.calls.append(path)
        if path=='/api/v1/key':return {'data':{'limit':0}}
        return {'data':[{'id':i.removeprefix('openrouter:'),'pricing':{'prompt':'0','completion':'0'}} for i in self.m.APPROVED]}
    def probe(self,model):self.probes.append(model.id)
    def renew(self,rows=None,**kwargs):return self.m.renew(self.env,rows or self.rows,self.now,fetch=kwargs.get('fetch',self.fetch),probe=kwargs.get('probe',self.probe))
    def test_fresh_evidence_makes_no_provider_requests(self):
        rows=copy.deepcopy(self.rows)
        for r in rows:r['checked_at']=self.now-100
        result=self.renew(rows);self.assertEqual(result['requests'],0);self.assertFalse(result['changed']);self.assertEqual(self.probes,[]);self.assertEqual(self.calls,[])
    def test_due_models_use_two_metadata_reads_and_one_probe_each(self):
        result=self.renew();self.assertEqual(result['status'],'PASS');self.assertEqual(result['requests'],4)
        self.assertEqual(self.calls,['/api/v1/key','/api/v1/models']);self.assertEqual(self.probes,list(self.m.APPROVED))
        self.assertTrue(all(r['checked_at']==self.now and r['native_tools_verified'] is False for r in result['records']))
    def test_only_the_due_model_is_probed(self):
        self.rows[1]['checked_at']=self.now-100
        result=self.renew();self.assertEqual(result['requests'],3);self.assertEqual(self.probes,[self.m.APPROVED[0]])
    def test_expired_previously_reviewed_models_can_recover(self):
        for r in self.rows:r['checked_at']=self.now-100000
        self.assertEqual(self.renew()['status'],'PASS')
    def test_rotated_key_cannot_be_silently_reauthorized(self):
        self.env['ABAP_ASSISTANT_OPENROUTER_KEY']='rotated-fixture-key'
        with self.assertRaises(self.m.RenewalError):self.renew()
        self.assertEqual(self.calls,[])
    def test_extra_model_or_unrestricted_configuration_is_rejected(self):
        for setting,value in [('ABAP_ASSISTANT_OPENROUTER_MODELS','vendor/paid'),('ABAP_ASSISTANT_DEMO_ONLY','false'),
            ('ABAP_ASSISTANT_N8N_WORKFLOWS','live-workflow'),('ABAP_ASSISTANT_REMOTE_APPROVED','false')]:
            with patch.dict(self.env,{setting:value}):
                with self.assertRaises((self.m.RenewalError,ValueError)):self.renew()
        self.assertEqual(self.calls,[])
    def test_nonzero_or_unlimited_key_limit_invalidates_without_inference(self):
        for limit in [1,None]:
            def fetch(*args):return {'data':{'limit':limit}}
            result=self.renew(fetch=fetch);self.assertTrue(result['changed']);self.assertEqual(result['requests'],1)
            self.assertTrue(all(r['access_verified'] is False for r in result['records']))
        self.assertEqual(self.probes,[])
    def test_no_longer_free_models_are_invalidated_without_probe(self):
        def fetch(host,path,headers=None):return {'data':{'limit':0}} if path.endswith('/key') else {'data':[]}
        result=self.renew(fetch=fetch);self.assertTrue(all(not r['free_eligible'] for r in result['records']));self.assertEqual(self.probes,[])
    def test_metadata_failure_does_not_extend_or_destroy_previous_evidence(self):
        previous=copy.deepcopy(self.rows)
        def fail(*args):raise ValueError('private-key-and-provider-body')
        result=self.renew(fetch=fail);self.assertFalse(result['changed']);self.assertEqual(self.rows,previous)
        self.assertNotIn('private-key',json.dumps(result))
    def test_partial_failure_preserves_failed_timestamp_and_renews_other_model(self):
        def probe(model):
            if model.id==self.m.APPROVED[0]:raise ValueError('private-key-and-provider-body')
        result=self.renew(probe=probe);byid={r['id']:r for r in result['records']}
        self.assertEqual(byid[self.m.APPROVED[0]]['checked_at'],self.now-70000)
        self.assertEqual(byid[self.m.APPROVED[1]]['checked_at'],self.now);self.assertNotIn('private-key',json.dumps(result))
    def test_combined_probe_checks_both_languages_and_exact_business_json(self):
        from assistant_gateway import Model
        answer=json.dumps({'english':'CLOUD_OK','japanese':'確認しました。','business_request':{'tool':'leads'}})
        model=Model(self.m.APPROVED[0],'openrouter',self.m.APPROVED[0].removeprefix('openrouter:'),'fixture-key')
        with patch('assistant_gateway.Gateway.generate',return_value=(answer,{})) as generate:self.m.combined_probe(model)
        self.assertEqual(generate.call_count,1)
        with patch('assistant_gateway.Gateway.generate',return_value=('```json\n'+answer+'\n```',{})):
            self.m.combined_probe(model)
        with patch('assistant_gateway.Gateway.generate',return_value=('{"tool":"start_workflow"}',{})):
            with self.assertRaises(self.m.RenewalError):self.m.combined_probe(model)
    def make_proof(self,d):
        p=Path(d)/'cloud-validation.json';raw=(json.dumps(self.rows)+'\n').encode();p.write_bytes(raw);p.chmod(0o640);os.chown(p,0,10001);return p,raw
    def test_atomic_directory_publication_preserves_permissions_and_key(self):
        with tempfile.TemporaryDirectory() as d:
            p,raw=self.make_proof(d);key=Path(d)/'openrouter-key';key.write_bytes(b'private-fixture-key')
            # An already-open file descriptor demonstrates why file bind mounts
            # retain old evidence; the directory path sees atomic replacement.
            with p.open('rb') as held:
                records=self.renew()['records'];self.m.atomic_publish(p,raw,records)
                self.assertEqual(held.read(),raw);self.assertEqual(json.loads(p.read_bytes()),records)
            self.assertEqual(key.read_bytes(),b'private-fixture-key');self.assertEqual(p.stat().st_gid,10001);self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o640)
    def test_operator_update_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p,raw=self.make_proof(d);replacement=json.dumps(self.rows,indent=4).encode();p.write_bytes(replacement)
            with self.assertRaises(self.m.RenewalError):self.m.atomic_publish(p,raw,self.rows)
            self.assertEqual(p.read_bytes(),replacement);self.assertEqual(list(Path(d).glob('.cloud-validation-*')),[])
    def test_failed_atomic_replace_preserves_last_good_file(self):
        with tempfile.TemporaryDirectory() as d:
            p,raw=self.make_proof(d)
            with patch.object(self.m.os,'replace',side_effect=OSError('fixture')):
                with self.assertRaises(OSError):self.m.atomic_publish(p,raw,self.rows)
            self.assertEqual(p.read_bytes(),raw);self.assertEqual(list(Path(d).glob('.cloud-validation-*')),[])
    def test_host_publishes_partial_success_without_logging_proof(self):
        def probe(model):
            if model.id==self.m.APPROVED[0]:raise ValueError('fixture-provider-failure')
        renewed=self.renew(probe=probe)
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)/'credentials';directory.mkdir(mode=0o750);os.chown(directory,0,10001)
            runtime=Path(d)/'runtime';runtime.mkdir(mode=0o700);proof,_=self.make_proof(directory)
            info={'Mounts':[{'Type':'bind','Source':str(directory),'Destination':self.m.CONTAINER_DIRECTORY,'RW':False}]}
            outputs=[b'owned-web\n',json.dumps([info]).encode(),json.dumps(renewed).encode()]
            with patch.object(self.m,'HOST_DIRECTORY',directory),patch.object(self.m,'PROOF',proof),patch.object(self.m,'LOCK',runtime/'renew.lock'),patch.object(self.m,'docker',side_effect=outputs):
                result=self.m.host_main()
            self.assertEqual(result['status'],'PARTIAL_OR_REVIEW_REQUIRED');self.assertNotIn('records',result)
            rows=json.loads(proof.read_bytes());self.assertEqual(rows[0]['checked_at'],self.now-70000);self.assertEqual(rows[1]['checked_at'],self.now)
    def test_host_refuses_old_individual_file_mount_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)/'credentials';directory.mkdir(mode=0o750);os.chown(directory,0,10001)
            runtime=Path(d)/'runtime';runtime.mkdir(mode=0o700);proof,_=self.make_proof(directory)
            with patch.object(self.m,'HOST_DIRECTORY',directory),patch.object(self.m,'PROOF',proof),patch.object(self.m,'LOCK',runtime/'renew.lock'),patch.object(self.m,'docker',side_effect=[b'owned-web\n',b'[{"Mounts":[]}]']) as docker:
                with self.assertRaises(self.m.RenewalError):self.m.host_main()
            self.assertEqual(docker.call_count,2) # Inspect only; no exec/provider call.
if __name__=='__main__':unittest.main()
