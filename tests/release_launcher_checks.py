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
            strict.command_value(['--sjasm', '/checked/sjasmplus'])

    def test_bare_noop_never_calls_release_build(self):
        invoked = []
        module.main = lambda: invoked.append(True)
        with patch.object(sys, 'argv', ['release_v1_strict.py',
                                       '--fuse-test-command', 'true']):
            with self.assertRaises(RuntimeError):
                strict.main()
        self.assertEqual(invoked, [])

    def test_authentic_boot_callback_required_once(self):
        expected = [sys.executable, 'tests/fuse_boot.py', '--expect-zxux-login']
        calls = []
        def original_run(cmd, env=None, log=None):
            calls.append(('run', cmd))
            return 'success'
        def main():
            module.run(expected)
        callback = lambda p: 'local-content-verified'
        with patch.object(module, 'run', original_run), \
             patch.object(module, 'main', main), \
             patch.object(module, 'validated_file', callback, create=True), \
             patch.object(strict, 'validate_boot_command', return_value=(expected, {'tape':'built'})), \
             patch.object(strict, 'validate_boot_proof') as validate, \
             patch.object(sys, 'argv', ['release_v1_strict.py', '--fuse-test-command', 'bound']):
            strict.main()
            validate.assert_called_once_with({'tape':'built'}, callback)
            self.assertEqual(calls, [('run', expected)])

    def test_missing_actual_boot_execution_rejected(self):
        expected = [sys.executable, 'tests/fuse_boot.py', '--expect-zxux-login']
        with patch.object(module, 'run', lambda cmd, env=None, log=None: 'ok'), \
             patch.object(module, 'main', lambda: None), \
             patch.object(module, 'validated_file', lambda p: None, create=True), \
             patch.object(strict, 'validate_boot_command', return_value=(expected, {})), \
             patch.object(sys, 'argv', ['release_v1_strict.py', '--fuse-test-command', 'bound']):
            with self.assertRaisesRegex(RuntimeError, 'not completed'):
                strict.main()


if __name__ == '__main__':
    unittest.main()
