"""Fail-closed tests for the ZX-UX release's independent FUSE gate."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

MODULE = Path(__file__).resolve().parent.parent / 'tools/fuse_release_gate.py'
spec = importlib.util.spec_from_file_location('fuse_release_gate', MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class FuseGateChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.build = self.root / 'build'
        self.build.mkdir()
        self.rom = self.root / 'ref.rom'
        self.fuse = self.root / 'fuse-sdl'
        self.assets = self.root / 'fuse-assets'
        self.lib = self.root / 'lib'
        self.screen = self.build / 'proofs' / 'boot.png'
        self.tape = self.build / 'ZX-UX.tzx'

    def command(self, *, tape=None, screen=None, end='--expect-zxux-login'):
        return ('%s -B tests/fuse_boot.py --fuse %s --rom %s '
                '--tape %s --assets %s --libdir %s --screen %s %s' %
                (sys.executable, self.fuse, self.rom, tape or self.tape,
                 self.assets, self.lib, screen or self.screen, end))

    def test_exact_new_build_path_and_login_mode(self):
        argv, paths = gate.validate_boot_command(self.command(), self.root,
                                                 self.build, sys.executable)
        self.assertEqual(paths['tape'], self.tape)
        self.assertEqual(paths['json'], self.screen.with_suffix('.json'))
        self.assertIn('--expect-zxux-login', argv)

    def test_bare_success_command_does_not_count(self):
        with self.assertRaises(RuntimeError):
            gate.validate_boot_command('true', self.root, self.build, sys.executable)

    def test_unrelated_python_module_does_not_count(self):
        with self.assertRaises(RuntimeError):
            gate.validate_boot_command(sys.executable + ' -c pass', self.root,
                                       self.build, sys.executable)

    def test_stale_tape_rejected(self):
        with self.assertRaises(RuntimeError):
            gate.validate_boot_command(self.command(tape=self.root / 'stale.tzx'),
                                       self.root, self.build, sys.executable)

    def test_text_only_mode_rejected(self):
        with self.assertRaises(RuntimeError):
            gate.validate_boot_command(self.command(end='--expected-text ZX-UX'),
                                       self.root, self.build, sys.executable)

    def test_outside_capture_rejected(self):
        with self.assertRaises(RuntimeError):
            gate.validate_boot_command(self.command(screen=self.root / 'elsewhere.png'),
                                       self.root, self.build, sys.executable)

    def test_duplicate_argument_rejected(self):
        with self.assertRaises(RuntimeError):
            gate.validate_boot_command(self.command(end='--expect-zxux-login --expect-zxux-login'),
                                       self.root, self.build, sys.executable)

    def test_unknown_argument_rejected(self):
        with self.assertRaises(RuntimeError):
            gate.validate_boot_command(self.command(end='--expect-zxux-login --foo bar'),
                                       self.root, self.build, sys.executable)

    def test_output_cannot_pass_without_real_inputs(self):
        _, paths = gate.validate_boot_command(self.command(), self.root,
                                              self.build, sys.executable)
        with self.assertRaises(RuntimeError):
            gate.validate_boot_proof(paths, lambda p: None)


if __name__ == '__main__':
    unittest.main()
