"""Verify strict release rejects unbound boot commands before building."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
module = types.ModuleType('release_v1')
module.ROOT = HERE.parent
module.BUILD = HERE.parent / 'build'
module.PYTHON = sys.executable
module.run = lambda *a, **kw: None
module.main = lambda: None

with patch.dict(sys.modules, {'release_v1': module}):
    with patch.object(sys, 'path', [str(HERE.parent / 'tools')] + sys.path):
        spec = importlib.util.spec_from_file_location('release_v1_strict',
                                                      HERE.parent / 'tools/release_v1_strict.py')
        strict = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strict)


class StrictReleaseTests(unittest.TestCase):
    def test_duplicate_fuse_command_rejected(self):
        with self.assertRaises(RuntimeError):
            strict.command_value(['--fuse-test-command', 'true',
                                  '--fuse-test-command', 'true'])

    def test_missing_fuse_command_rejected(self):
        with self.assertRaises(RuntimeError):
            strict.command_value(['--checker', '/private/checker.py'])

    def test_bare_noop_never_calls_release_build(self):
        invoked = []
        module.main = lambda: invoked.append(True)
        with patch.object(sys, 'argv', ['release_v1_strict.py',
                                       '--fuse-test-command', 'true']):
            with self.assertRaises(RuntimeError):
                strict.main()
        self.assertEqual(invoked, [])


if __name__ == '__main__':
    unittest.main()
