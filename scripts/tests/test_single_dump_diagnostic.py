"""New one-file wrapper checks only; no remote client or live database."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
from contextlib import ExitStack

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('single_dump',ROOT/'deploy/hosthatch/retrieve-one-dump-and-diagnose-once.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SingleDumpTests(unittest.TestCase):
    def test_retain_is_private_atomic_and_never_overwrites(self):
        data=b'synthetic private fixture';entry=(*m.ENTRY[:3],len(data),hashlib.sha256(data).hexdigest())
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ENTRY',entry),patch.object(m,'CACHE',Path(t)/'cache'),patch.object(m,'DEST',Path(t)/'cache/database.dump'):
            m.retain(data);self.assertEqual(m.DEST.read_bytes(),data)
            self.assertEqual(stat.S_IMODE(m.CACHE.stat().st_mode),0o700)
            self.assertEqual(stat.S_IMODE(m.DEST.stat().st_mode),0o600)
            with self.assertRaises(FileExistsError):m.retain(data)
            self.assertEqual(m.DEST.read_bytes(),data)
            self.assertEqual([p.name for p in m.CACHE.iterdir()],['database.dump'])

    def test_invalid_bytes_never_create_a_cache(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'CACHE',Path(t)/'cache'):
            with self.assertRaises(m.Stop):m.retain(b'corrupted')
            self.assertFalse(m.CACHE.exists())

    def test_reviewed_helpers_remain_unchanged(self):
        for name,h in m.SOURCES.items():self.assertEqual(hashlib.sha256((ROOT/'deploy/hosthatch'/name).read_bytes()).hexdigest(),h)

    def fixtures(self,existing=None,fetch_failure=False,quota_failure=False):
        stack=ExitStack();self.addCleanup(stack.close)
        for name in ['ROOT','CACHE','DEST','RECEIPT']:
            obj=Mock();obj.exists.return_value=False;obj.is_symlink.return_value=False
            stack.enter_context(patch.object(m,name,obj))
        stack.enter_context(patch.object(m,'private_directory'))
        self.saved=stack.enter_context(patch.object(m,'save'))
        self.retained=stack.enter_context(patch.object(m,'retain'))
        stack.enter_context(patch.object(m,'existing_dump',side_effect=[existing,b'verified',b'verified']))
        stack.enter_context(patch.object(m.shutil,'disk_usage',return_value=types.SimpleNamespace(free=2000000000)))
        stack.enter_context(patch.object(m.Path,'read_text',return_value='MemAvailable: 3000000\n'))
        stack.enter_context(patch.object(m.Path,'lstat',return_value=types.SimpleNamespace(st_mode=0o100600,st_uid=0)))
        class Guard(Exception):pass
        fetch=types.SimpleNamespace(Guard=Guard,quota_gate=Mock(return_value={'status':'PASS'}),retrieve=Mock(return_value=b'verified'))
        if fetch_failure:fetch.retrieve.side_effect=Guard('targeted_read_failed')
        if quota_failure:fetch.quota_gate.side_effect=Guard('provider_allowance_confirmation_stale')
        receipt=Mock();receipt.exists.return_value=False;receipt.is_symlink.return_value=False
        d=types.SimpleNamespace(RECEIPT=receipt,Stop=Guard,IMAGE='cached-image',__file__='reviewed-diagnostic.py',
            inspect_existing=Mock(return_value=({'actionable_restore_error_recovered':False},[])),
            docker=Mock(return_value=types.SimpleNamespace(stdout=json.dumps([{'Id':'cached-image'}]).encode())),
            main=Mock(return_value={'status':'FAIL-isolated-restore-only','restore_attempts':1,'postgresql_error':{'sqlstates':['42704']}}))
        return fetch,d

    def test_one_exact_read_one_diagnostic_and_retention_on_restore_failure(self):
        fetch,d=self.fixtures();answer=m.perform(fetch,d,{})
        fetch.retrieve.assert_called_once();self.assertEqual(fetch.retrieve.call_args.args[1],m.ENTRY)
        self.assertEqual(fetch.FILES,[m.ENTRY]);d.main.assert_called_once();self.retained.assert_called_once_with(b'verified')
        self.assertTrue(answer['verified_dump_still_retained']);self.assertEqual(answer['restore_attempts'],1)
        self.assertEqual(answer['diagnostic']['postgresql_error']['sqlstates'],['42704'])

    def test_failed_retrieval_never_retries_or_runs_restore(self):
        fetch,d=self.fixtures(fetch_failure=True);answer=m.perform(fetch,d,{})
        fetch.retrieve.assert_called_once();d.main.assert_not_called();self.retained.assert_not_called()
        self.assertEqual(answer['retrieval_invocations'],1)

    def test_existing_verified_copy_avoids_provider_and_quota_requests(self):
        fetch,d=self.fixtures(existing=b'verified');m.perform(fetch,d,{})
        fetch.retrieve.assert_not_called();fetch.quota_gate.assert_not_called();d.main.assert_called_once()

    def test_stale_or_insufficient_allowance_stops_before_remote_read(self):
        fetch,d=self.fixtures(quota_failure=True)
        with self.assertRaises(fetch.Guard):m.perform(fetch,d,{})
        fetch.retrieve.assert_not_called();d.main.assert_not_called();self.saved.assert_not_called()

if __name__=='__main__':unittest.main()
