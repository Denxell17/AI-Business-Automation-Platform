"""New install boundaries in disposable local container; no production calls."""
from pathlib import Path
import runpy
import stat
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
m=runpy.run_path(str(ROOT/'deploy/hosthatch/install-n8n-recurring-staging-fix.py'));g=m['main'].__globals__
class RecurringInstallTests(unittest.TestCase):
    def test_payload_checksums_match_reviewed_files(self):
        for name,(_,_,expected) in m['FILES'].items():
            self.assertEqual(m['sha']((ROOT/'deploy/hosthatch'/name).read_bytes()),expected)

    def test_exclusive_backup_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'original';m['write_new'](p,b'preserved',0o600)
            with self.assertRaises(FileExistsError):m['write_new'](p,b'replaced',0o600)
            self.assertEqual(p.read_bytes(),b'preserved')

    def test_replacement_preserves_ownership_and_permissions(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'target';m['write_new'](p,b'old',0o750);before=p.stat()
            m['replace'](p,b'new',before);after=p.stat()
            self.assertEqual(p.read_bytes(),b'new')
            self.assertEqual((before.st_uid,before.st_gid,stat.S_IMODE(before.st_mode)),(after.st_uid,after.st_gid,stat.S_IMODE(after.st_mode)))
            self.assertEqual([x.name for x in Path(root).iterdir()],['target'])

    def test_restore_originals_restores_both_already_changed_targets(self):
        with tempfile.TemporaryDirectory() as root:
            files={};previous={};metadata={}
            for name in ['one','two']:
                p=Path(root)/name;data=('original-'+name).encode()
                m['write_new'](p,data,0o750);metadata[name]=p.stat();previous[name]=data
                files[name]=(str(p),m['sha'](data),'unused');p.write_bytes(b'changed')
            with patch.dict(g,FILES=files):self.assertEqual(m['restore_originals'](['one','two'],previous,metadata),[])
            for name in files:self.assertEqual((Path(root)/name).read_bytes(),previous[name])

    def test_symlink_and_writable_targets_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'target';m['write_new'](p,b'old',0o750)
            link=Path(root)/'link';link.symlink_to(p)
            with self.assertRaises(m['Stop']):m['read_trusted'](link)
            p.chmod(0o770)
            with self.assertRaises(m['Stop']):m['read_trusted'](p)

    def test_missing_explicit_mode_stops_before_production_access(self):
        with patch.object(m['sys'],'argv',['installer']),patch.dict(g,read_trusted=lambda *a:self.fail('production read')):
            with self.assertRaisesRegex(m['Stop'],'explicit_authenticated_install_approval_required'):m['main']()

if __name__=='__main__':unittest.main()
