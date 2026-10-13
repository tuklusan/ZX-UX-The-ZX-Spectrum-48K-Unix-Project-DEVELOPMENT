"""Tests for narrow release-log delivery exceptions."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import mkrelease


class ReleaseDiagnosticCopyChecks(unittest.TestCase):
    def test_only_empty_fuse_streams_are_excluded(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            logs = root / 'logs'
            logs.mkdir()
            (logs / 'fuse-login.stdout.txt').write_bytes(b'')
            (logs / 'fuse-login.stderr.txt').write_bytes(b'')
            (logs / 'system-regression.txt').write_text('PASS\n')
            (logs / 'other.txt').write_bytes(b'')
            target = root / 'release'
            with patch.object(mkrelease, 'ROOT', root), patch.object(mkrelease, 'RELEASE', target), redirect_stdout(StringIO()):
                mkrelease.copy_logs(logs)
            self.assertFalse((target / 'logs/fuse-login.stdout.txt').exists())
            self.assertFalse((target / 'logs/fuse-login.stderr.txt').exists())
            self.assertEqual((target / 'logs/system-regression.txt').read_text(), 'PASS\n')
            self.assertTrue((target / 'logs/other.txt').exists())

    def test_c48_reports_and_env1_images_are_delivered(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / 'build'
            (build / 'logs').mkdir(parents=True)
            (build / 'c48-env1' / 'proof').mkdir(parents=True)
            for name in ('c48-conformance.json', 'ix-abi-proof.json',
                         'native-env1-v1.json'):
                (build / 'logs' / name).write_text('{"result":"PASS"}\n')
            for name in ('sequential-1.png', 'sequential-1.scr',
                         'sequential-2.png', 'sequential-2.scr',
                         'concurrent.png', 'concurrent.scr'):
                (build / 'c48-env1' / 'proof' / name).write_bytes(name.encode())
            release = root / 'release'
            with patch.object(mkrelease, 'ROOT', root), patch.object(mkrelease, 'BUILD', build), patch.object(mkrelease, 'RELEASE', release), redirect_stdout(StringIO()):
                mkrelease.copy_fresh_proofs()
            self.assertEqual((release / 'proofs/c48-conformance.json').read_text(), '{"result":"PASS"}\n')
            self.assertEqual((release / 'proofs/native-env1/concurrent.scr').read_bytes(), b'concurrent.scr')
            self.assertEqual(len(list((release / 'proofs').rglob('*.*'))), 9)

    def test_missing_required_env1_capture_blocks_copy(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / 'build'
            (build / 'logs').mkdir(parents=True)
            for name in ('c48-conformance.json', 'ix-abi-proof.json',
                         'native-env1-v1.json'):
                (build / 'logs' / name).write_text('{}\n')
            with patch.object(mkrelease, 'ROOT', root), patch.object(mkrelease, 'BUILD', build), patch.object(mkrelease, 'RELEASE', root / 'release'), redirect_stdout(StringIO()):
                with self.assertRaises(SystemExit):
                    mkrelease.copy_fresh_proofs()

    def test_nonempty_emulator_error_is_preserved(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            logs = root / 'logs'
            logs.mkdir()
            (logs / 'fuse-login.stderr.txt').write_text('emulator diagnostic\n')
            target = root / 'release'
            with patch.object(mkrelease, 'ROOT', root), patch.object(mkrelease, 'RELEASE', target), redirect_stdout(StringIO()):
                mkrelease.copy_logs(logs)
            self.assertEqual((target / 'logs/fuse-login.stderr.txt').read_text(),
                             'emulator diagnostic\n')


if __name__ == '__main__':
    unittest.main()
