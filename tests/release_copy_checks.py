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
