import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path('/workspace')
class ApprovedReleaseGuards(unittest.TestCase):
    def setUp(self):
        s=importlib.util.spec_from_file_location('release',ROOT/'deploy/production/release-advanced-assistant.py');self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m)
    def configs(self):
        before={'services':{'database':{'image':'existing'},'worker':{'image':'existing'},'web':{'environment':{'DATABASE_URL':'private-canary'},'volumes':[{'target':'/app/data'}]}}}
        after=copy.deepcopy(before);after['services']['web']['environment']['ABAP_ASSISTANT_DEMO_ONLY']='true'
        return before,after
    def test_existing_services_and_business_environment_must_be_preserved(self):
        a,b=self.configs();self.m.config_preserved(a,b)
        b['services']['worker']['image']='wrong'
        with self.assertRaises(self.m.Stop):self.m.config_preserved(a,b)
        a,b=self.configs();b['services']['web']['environment']['DATABASE_URL']='wrong'
        with self.assertRaises(self.m.Stop):self.m.config_preserved(a,b)
    def test_existing_volumes_cannot_be_removed(self):
        a,b=self.configs();b['services']['web']['volumes']=[]
        with self.assertRaises(self.m.Stop):self.m.config_preserved(a,b)
    def proof(self):
        return [{'id':name,'key_fingerprint':self.m.sha(b'fixture-key'),'checked_at':1000,**{k:True for k in ['free_eligible','access_verified','business_protocol_verified','english_verified','japanese_verified']}} for name in self.m.MODELS]
    def test_matching_current_proof_required(self):
        self.m.validate_proof(b'fixture-key',self.proof(),2000)
        for key,now in [(b'wrong-key',2000),(b'fixture-key',100000)]:
            with self.assertRaises(self.m.Stop):self.m.validate_proof(key,self.proof(),now)
    def test_paid_or_additional_model_is_rejected(self):
        p=self.proof();p[0]['id']='openrouter:paid'
        with self.assertRaises(self.m.Stop):self.m.validate_proof(b'fixture-key',p,2000)
    def test_install_never_overwrites_existing_files(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'original';p.write_bytes(b'original')
            with self.assertRaises(FileExistsError):self.m.write_new(p,b'replacement')
            self.assertEqual(p.read_bytes(),b'original')
    def test_rollback_replaces_only_web_using_original_overlay(self):
        with patch.object(self.m,'compose') as compose,patch.object(self.m,'inventory',return_value=[]),patch.object(self.m,'service',return_value={'Image':self.m.OLD}),patch.object(self.m,'baseline_smoke',return_value={'ready':200}):
            self.assertEqual(self.m.rollback_web(False)['status'],'PASS')
        self.assertEqual(compose.call_args.args,(['rollback-web.json'],'up','-d','--no-deps','--no-build','--pull','never','web'))
if __name__=='__main__':unittest.main()
