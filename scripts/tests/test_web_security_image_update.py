"""Focused image-only deployment boundary checks, no Docker or production calls."""
import copy
from pathlib import Path
import runpy
import unittest

m=runpy.run_path(str(Path(__file__).resolve().parents[2]/'deploy/production/apply-web-security-image-once.py'))

class WebSecurityUpdateTests(unittest.TestCase):
    def setUp(self):
        self.before={'name':'abap-deploy','secrets':{'existing':{'file':'/private/source'}},'services':{
            'web':{'image':'old','environment':{'DEMO':'true'},'volumes':[{'source':'old','target':'/data','read_only':True}]},
            'database':{'image':'postgres'}}}
        self.after=copy.deepcopy(self.before);self.after['services']['web']['image']=m['TAG']

    def test_exact_image_only_change_admitted(self):m['image_only'](self.before,self.after)

    def test_environment_mount_other_service_and_secret_changes_rejected(self):
        for field in ['environment','mount','database','secret','extra_service']:
            with self.subTest(field=field):
                after=copy.deepcopy(self.after)
                if field=='environment':after['services']['web']['environment']['DEMO']='false'
                if field=='mount':after['services']['web']['volumes'][0]['read_only']=False
                if field=='database':after['services']['database']['image']='changed'
                if field=='secret':after['secrets']['existing']['file']='/different/source'
                if field=='extra_service':after['services']['unexpected']={}
                with self.assertRaises(m['Stop']):m['image_only'](self.before,after)

    def test_wrong_image_and_in_place_input_mutation_rejected(self):
        self.after['services']['web']['image']='unreviewed'
        with self.assertRaises(m['Stop']):m['image_only'](self.before,self.after)
        self.assertEqual(self.before['services']['web']['image'],'old')

if __name__=='__main__':unittest.main()
