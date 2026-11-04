"""Installation delta guards only; no Docker, providers or production access."""
import copy
import runpy
import unittest
from pathlib import Path

INSTALL = runpy.run_path(str(Path(__file__).resolve().parents[2] /
                            'deploy/hosthatch/install-assistant-validation-renewal.py'))


class InstallationDeltaTests(unittest.TestCase):
    def setUp(self):
        self.before = {'networks': {'default': {'name': 'existing'}}, 'services': {
            'database': {'image': 'postgres:18'},
            'web': {'image': 'unchanged', 'environment': {
                'ABAP_ASSISTANT_CLOUD_VALIDATION_FILE': '/old/proof', 'DEMO': 'true'},
                'volumes': [{'type': 'volume', 'source': 'existing', 'target': '/data'}]}}}
        self.after = copy.deepcopy(self.before)
        self.after['services']['web']['environment']['ABAP_ASSISTANT_CLOUD_VALIDATION_FILE'] = \
            '/run/assistant-validation/cloud-validation.json'
        self.after['services']['web']['volumes'].append({
            'type': 'bind', 'source': str(INSTALL['KEY'].parent),
            'target': '/run/assistant-validation', 'read_only': True,
            'bind': {'create_host_path': False}})

    def test_exact_approved_delta(self):
        INSTALL['verify_delta'](self.before, self.after)

    def test_unrelated_changes_rejected(self):
        for change in ('environment', 'image', 'service', 'network', 'old_volume'):
            with self.subTest(change=change):
                after = copy.deepcopy(self.after)
                if change == 'environment': after['services']['web']['environment']['DEMO'] = 'false'
                if change == 'image': after['services']['web']['image'] = 'different'
                if change == 'service': after['services']['extra'] = {}
                if change == 'network': after['networks'] = {}
                if change == 'old_volume': after['services']['web']['volumes'].pop(0)
                with self.assertRaises(INSTALL['Stop']):
                    INSTALL['verify_delta'](self.before, after)

    def test_unsafe_bind_rejected(self):
        for field, value in [('read_only', False), ('source', '/etc'), ('target', '/wrong')]:
            with self.subTest(field=field):
                after = copy.deepcopy(self.after)
                after['services']['web']['volumes'][-1][field] = value
                with self.assertRaises(INSTALL['Stop']):
                    INSTALL['verify_delta'](self.before, after)


if __name__ == '__main__':
    unittest.main()
