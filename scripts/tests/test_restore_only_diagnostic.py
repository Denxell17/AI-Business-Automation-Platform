"""New diagnostic boundaries only; no Docker, B2 or production access."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

SOURCE=Path(__file__).resolve().parents[2]/'deploy/hosthatch/diagnose-existing-postgresql-restore.py'
spec=importlib.util.spec_from_file_location('restore_only_diagnostic',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RestoreDiagnosticTests(unittest.TestCase):
    def test_error_categories_sqlstate_and_statement_are_useful_without_private_data(self):
        raw=b'pg_restore: error: could not execute query: ERROR: role "PRIVATE_CUSTOMER_TOKEN" does not exist\nERROR:  42704: role missing\nCommand was: ALTER TABLE "PRIVATE_TABLE" OWNER TO "PRIVATE_CUSTOMER_TOKEN";'
        result=m.sanitize(raw);encoded=json.dumps(result)
        self.assertIn('role_missing',result['categories']);self.assertIn('42704',result['sqlstates'])
        self.assertEqual(result['statement_type'],'ALTER');self.assertNotIn('PRIVATE',encoded)
        self.assertFalse(result['raw_text_retained'])

    def test_unknown_error_fails_closed_without_echoing_tokens_urls_or_business_data(self):
        secret='PRIVATE_SECRET_0123456789'
        result=m.sanitize(('Unexpected https://private.example/'+secret+' email=customer@example.invalid').encode())
        self.assertEqual(result['categories'],['unclassified_postgresql_error'])
        self.assertNotIn(secret,json.dumps(result));self.assertNotIn('private.example',json.dumps(result))

    def test_connection_and_archive_failures_are_distinct(self):
        self.assertIn('connection_failure',m.sanitize(b'pg_restore: error: connection to server on socket failed')['categories'])
        self.assertIn('unsupported_archive_version',m.sanitize(b'pg_restore: error: unsupported version (1.99) in file header')['categories'])

    def mode(self,inspection,verified):
        root=MagicMock();root.resolve.return_value=root
        root.stat.return_value=types.SimpleNamespace(st_uid=0,st_mode=0o40700)
        with patch.object(m,'ROOT',root),patch.object(m.os,'geteuid',return_value=0,create=True),\
             patch.object(m.os,'umask'),patch.object(sys,'argv',['diagnostic','--approved-restore-if-local']),\
             patch.object(m,'inspect_existing',return_value=(inspection,verified)),\
             patch.object(m,'restore_once') as restore,patch.object(m,'docker') as docker:
            result=m.main();restore.assert_not_called();docker.assert_not_called();return result

    def test_missing_verified_input_never_starts_a_container_or_retrieves_data(self):
        result=self.mode({'actionable_restore_error_recovered':False},[])
        self.assertEqual(result['status'],'BLOCKED-verified-local-dump-unavailable')
        self.assertEqual(result['restore_attempts'],0);self.assertEqual(result['b2_requests'],0)

    def test_recovered_error_avoids_even_an_authorized_restore(self):
        result=self.mode({'actionable_restore_error_recovered':True},[Path('/verified/dump')])
        self.assertEqual(result['status'],'PASS-existing-restore-error-recovered')

    def test_image_import_retrieval_and_unrelated_service_operations_are_forbidden(self):
        with patch.object(m.subprocess,'run') as run:
            for args in [('image','load'),('image','pull'),('image','save'),('load',),('pull',),('compose',),('restart',),('stop',)]:
                with self.subTest(args=args),self.assertRaises(m.Stop):m.docker(*args)
            run.assert_not_called()

if __name__=='__main__':unittest.main()
