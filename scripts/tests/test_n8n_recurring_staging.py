"""Only new per-run staging/cleanup behavior; isolated root filesystem required."""
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('recurring_state',ROOT/'deploy/hosthatch/n8n_backup_state.py')
state=importlib.util.module_from_spec(spec);spec.loader.exec_module(state)

class RecurringStagingTests(unittest.TestCase):
    def setUp(self):
        self.parent=Path('/var/backups/n8n/runs');self.parent.mkdir(mode=0o700,exist_ok=True)
        self.run='run-'+'a'*32;self.bundle=self.parent/self.run
        self.legacy=Path('/var/backups/n8n/staging');self.legacy.mkdir(mode=0o700,exist_ok=True)
        (self.legacy/'protected.txt').write_text('synthetic preserved capture')

    def tearDown(self):
        # Only this fixture's two explicit paths, all within a disposable tmpfs.
        import shutil
        if self.bundle.is_symlink():self.bundle.unlink()
        elif self.bundle.exists():shutil.rmtree(self.bundle)
        if (self.parent/'outside').exists():shutil.rmtree(self.parent/'outside')

    def ready(self):
        state.create_run(self.bundle,self.run)
        for target in state.TARGETS:(self.bundle/target).mkdir(mode=0o700)

    def test_legacy_staging_is_never_a_cleanup_target(self):
        with self.assertRaises(state.CaptureError):state.cleanup_run(self.legacy,self.run)
        self.assertEqual((self.legacy/'protected.txt').read_text(),'synthetic preserved capture')

    def test_two_verified_captures_cleanup_only_own_run(self):
        self.ready()
        with patch.object(state,'verify',side_effect=lambda p:{'target':p.name}) as verify:
            state.cleanup_run(self.bundle,self.run)
        self.assertEqual(verify.call_count,2)
        self.assertFalse(self.bundle.exists());self.assertTrue(self.legacy.exists())

    def test_existing_run_is_not_overwritten(self):
        state.create_run(self.bundle,self.run)
        with self.assertRaises(state.CaptureError):state.create_run(self.bundle,self.run)

    def test_failed_capture_is_retained(self):
        self.ready()
        with patch.object(state,'verify',side_effect=state.CaptureError('synthetic invalid capture')):
            with self.assertRaises(state.CaptureError):state.cleanup_run(self.bundle,self.run)
        self.assertTrue(self.bundle.exists())

    def test_unknown_contents_and_changed_marker_are_retained(self):
        self.ready();(self.bundle/'unknown').write_text('retain')
        with self.assertRaises(state.CaptureError):state.cleanup_run(self.bundle,self.run)
        (self.bundle/'unknown').unlink();(self.bundle/'.run.json').write_text(json.dumps({'run_id':'wrong'}))
        with self.assertRaises(state.CaptureError):state.cleanup_run(self.bundle,self.run)

    def test_symlink_capture_is_retained(self):
        self.ready();target=next(iter(state.TARGETS));(self.bundle/target).rmdir()
        other=self.parent/'outside';other.mkdir();(other/'keep').write_text('synthetic')
        (self.bundle/target).symlink_to(other,target_is_directory=True)
        with self.assertRaises(state.CaptureError):state.cleanup_run(self.bundle,self.run)
        self.assertTrue((other/'keep').exists())

    def test_script_uses_one_budget_read_and_unchanged_repository_settings(self):
        script=(ROOT/'deploy/hosthatch/n8n-backup.sh').read_text()
        self.assertEqual(script.count('$(operations_restic_raw_bytes)'),1)
        self.assertIn('operations_report_restic_budget "$projected_bytes"',script)
        self.assertIn('operations_configure_restic',script)
        self.assertIn('cleanup --bundle "$STAGING_DIRECTORY" --run-id "$run_tag"',script)
        self.assertNotIn('STAGING_DIRECTORY="$STAGING_PARENT/staging"',script)
        self.assertNotIn('restic forget',script);self.assertNotIn('restic prune',script)

if __name__=='__main__':
    if os.geteuid()!=0:raise SystemExit('Run only in the disposable fixture container')
    unittest.main()
