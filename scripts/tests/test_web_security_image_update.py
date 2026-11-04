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

    def test_mount_order_only_is_equivalent_without_losing_options(self):
        mounts=[{'Type':'bind','Source':'/private/a','Target':'/run/a','ReadOnly':True},
                {'Type':'bind','Source':'/private/b','Target':'/run/b','ReadOnly':True}]
        before={'Mounts':mounts,'ReadonlyRootfs':True}
        after={'Mounts':list(reversed(mounts)),'ReadonlyRootfs':True}
        result=m['runtime_comparison'](before,after)
        self.assertEqual(result,{'raw_differing_fields':['Mounts'],'material_differing_fields':[],'equivalent':True})
        self.assertEqual(before['Mounts'],mounts)
        self.assertNotIn('/private',str(result))

    def test_real_runtime_changes_fail_and_only_field_names_are_reported(self):
        before={'Mounts':[{'Target':'/run/a','Source':'SECRET','ReadOnly':True}],
                'Privileged':False,'ReadonlyRootfs':True,'NetworkMode':'private','Memory':1024}
        for field in ['Mounts','Privileged','ReadonlyRootfs','NetworkMode','Memory']:
            after=copy.deepcopy(before)
            if field=='Mounts':after[field][0]['ReadOnly']=False
            elif field=='Privileged':after[field]=True
            else:after[field]='changed'
            result=m['runtime_comparison'](before,after)
            self.assertFalse(result['equivalent'])
            self.assertEqual(result['material_differing_fields'],[field])
            self.assertNotIn('SECRET',str(result))

    def test_duplicate_targets_and_added_fields_are_not_hidden(self):
        with self.assertRaises(m['Stop']):
            m['runtime_comparison']({'Mounts':[{'Target':'/x'},{'Target':'/x'}]}, {'Mounts':[]})
        self.assertFalse(m['runtime_comparison']({}, {'Mounts':[]})['equivalent'])

if __name__=='__main__':unittest.main()
