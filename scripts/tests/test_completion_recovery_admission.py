"""Exercise the changed image admission guards without starting any operation."""
import ast
from pathlib import Path
import types
import runpy
import datetime
import unittest

ROOT = Path(__file__).resolve().parents[2] / 'deploy/hosthatch'
CURRENT = 'sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49'
PRESERVED = 'sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9'


class RecoveryAdmissionTests(unittest.TestCase):
    def test_authenticated_console_proof_is_distinct_and_still_requires_fresh_capacity(self):
        module = runpy.run_path(str(ROOT / 'retrieve-and-continue-application-once.py'))
        now = datetime.datetime(2026, 11, 4, 10, 45, tzinfo=datetime.timezone.utc)
        proof = {'source': 'authenticated_backblaze_caps_alerts', 'caps_unchanged': True,
                 'checked_at_utc': now.isoformat(), 'utc_day': '2026-11-04',
                 'class_b_remaining': 2476, 'class_c_remaining': 2476,
                 'download_remaining_bytes': 900000000}
        self.assertEqual(module['quota_gate'](proof, now)['status'], 'PASS-authenticated-console-observed')
        for changes in [{'class_b_remaining': 0}, {'caps_unchanged': False}, {'source': 'unverified'},
                        {'checked_at_utc': (now-datetime.timedelta(minutes=16)).isoformat()}]:
            with self.assertRaises(module['Guard']):
                module['quota_gate']({**proof, **changes}, now)

    def test_deployed_release_admitted_without_changing_restored_release(self):
        for filename, marker in [
            ('continue-current-application-offline.py', 'production_release_drift'),
            ('retrieve-and-continue-application-once.py', 'production_image_drift'),
        ]:
            with self.subTest(controller=filename):
                tree = ast.parse((ROOT / filename).read_bytes())
                assigned = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                                and any(isinstance(t, ast.Name) and t.id == 'PRODUCTION_IMAGE' for t in node.targets))
                current = ast.literal_eval(assigned)
                guard = next(node.args[0] for node in ast.walk(tree) if isinstance(node, ast.Call)
                             and any(isinstance(arg, ast.Constant) and arg.value == marker for arg in node.args))
                expr = compile(ast.Expression(guard), filename, 'eval')
                for web, database, expected in [(CURRENT, 'db', True), (PRESERVED, 'db', False),
                                                ('unknown', 'db', False), (CURRENT, 'changed-db', False)]:
                    helper = types.SimpleNamespace(IMAGE=PRESERVED, DB_IMAGE='db',
                        service=lambda rows, service: rows[service])
                    rows = {'web': {'Image': web}, 'database': {'Image': database}}
                    self.assertEqual(eval(expr, {'p': helper, 'rows': rows, 'PRODUCTION_IMAGE': current}), expected)
                    self.assertEqual(helper.IMAGE, PRESERVED)

    def test_preserved_image_and_restore_inputs_unchanged(self):
        for filename in ['preserve-current-app-once.py', 'continue-current-application-offline.py']:
            tree = ast.parse((ROOT / filename).read_bytes())
            constants = {target.id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                         and isinstance(node.value, ast.Constant) for target in node.targets if isinstance(target, ast.Name)}
            if filename.startswith('preserve'):
                self.assertEqual(constants['IMAGE'], PRESERVED)
            else:
                self.assertEqual(constants['DB_SHA'], '25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761')
                self.assertEqual(constants['CONFIG_SHA'], '2281312dbb691abe693dfb2467361e951624c840654c126bbe64958c76e5d0d8')


if __name__ == '__main__':
    unittest.main()
