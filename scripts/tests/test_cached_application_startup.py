"""New continuation admission/redaction checks; no Docker/provider/backup calls."""
import ast
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

PATH=Path(__file__).resolve().parents[2]/'deploy/hosthatch/finish-application-startup-once.py'
m=runpy.run_path(str(PATH));g=m['main'].__globals__

class CachedStartupTests(unittest.TestCase):
    def test_unapproved_mode_stops_before_inspection(self):
        with patch.object(m['os'],'geteuid',return_value=0,create=True),patch.object(m['sys'],'argv',['controller']),patch.dict(g,load=lambda *a:self.fail('helper executed')):
            with self.assertRaisesRegex(m['Stop'],'separate_authenticated_approval_required'):m['main']()

    def test_nonroot_stops_before_inspection(self):
        with patch.object(m['os'],'geteuid',return_value=1000,create=True),patch.object(m['sys'],'argv',['controller','--approved-cached-startup']):
            with self.assertRaisesRegex(m['Stop'],'separate_authenticated_approval_required'):m['main']()

    def test_unit_summary_does_not_reveal_arguments_or_environment(self):
        raw='ActiveState=failed\nExecStart={ path=/usr/local/sbin/n8n-backup ; argv[]=/usr/local/sbin/n8n-backup --token SECRET_SENTINEL ; }\nReadWritePaths=/private/SECRET_SENTINEL\n'
        with patch.dict(g,run_readonly=lambda *a:raw):result=m['unit_summary']('n8n-backup.service')
        self.assertEqual(result['ExecStart_executables'],['/usr/local/sbin/n8n-backup'])
        self.assertNotIn('SECRET_SENTINEL',str(result))

    def test_unreviewed_helper_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'helper.py';p.write_text("raise RuntimeError('must not execute')")
            with patch.dict(g,__file__=str(Path(root)/'controller.py')):
                with self.assertRaisesRegex(m['Stop'],'reviewed_helper_checksum_mismatch'):m['load']('helper.py','0'*64)

    def test_link_probe_is_readonly_aggregate_without_record_values(self):
        ast.parse(m['LINK_PROBE'])
        self.assertIn('SET TRANSACTION READ ONLY',m['LINK_PROBE'])
        self.assertIn('statement_timeout=5000',m['LINK_PROBE'])
        self.assertIn('count(DISTINCT',m['LINK_PROBE'])
        for text in ['INSERT INTO','UPDATE ','DELETE FROM','DROP ','CREATE ']:self.assertNotIn(text,m['LINK_PROBE'])

    def test_readiness_targets_final_tcp_server_without_changing_restore(self):
        args=('exec','owned-id','pg_isready','-U','rehearsal_admin')
        self.assertEqual(m['final_server_args'](args),('exec','owned-id','pg_isready','-h','127.0.0.1','-U','rehearsal_admin'))
        restore=('exec','-i','owned-id','pg_restore','--single-transaction')
        self.assertEqual(m['final_server_args'](restore),restore)

if __name__=='__main__':unittest.main()
