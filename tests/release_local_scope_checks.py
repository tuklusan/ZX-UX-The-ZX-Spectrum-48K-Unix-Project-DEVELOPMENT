"""Local release gates remain strict without running the private pre-push checker."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'tools/release_v1.py'
spec = importlib.util.spec_from_file_location('zx_release_local', SRC)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class LocalReleaseChecks(unittest.TestCase):
    def test_no_checker_required_for_local_help(self):
        proc = subprocess.run([sys.executable, str(SRC), '--help'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn('--fuse-test-command', proc.stdout)
        self.assertNotIn('--checker', proc.stdout)

    def test_fuse_argument_is_still_required(self):
        proc = subprocess.run([sys.executable, str(SRC),
                               '--sjasm', 'sjasm', '--tap2sna', 'tap2sna'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn('--fuse-test-command', proc.stderr)

    def test_checker_argument_is_rejected(self):
        proc = subprocess.run([sys.executable, str(SRC),
                               '--sjasm', 'sjasm', '--tap2sna', 'tap2sna',
                               '--fuse-test-command', 'fuse', '--checker', 'checker.py'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn('unrecognized arguments', proc.stderr)

    def test_no_private_checker_invocations_in_local_driver(self):
        text = SRC.read_text()
        for forbidden in ("'--command'", "'--tree'", "'--checker'", 'checker=checker',
                          'check(checker,', "parser.add_argument('--checker'"):
            self.assertNotIn(forbidden, text)

    def test_all_original_mandatory_steps_retained(self):
        text = SRC.read_text()
        for name in ('release-self-tests', 'build', 'boot-image-static', 'c48-runtime',
                     'c48-abi-ix', 'c48-language', 'c48-coverage', 'c48-target-units',
                     'c48-target', 'assembler-comparison', 'rom-tape-boot',
                     'system-regression', 'c48-program-tapes', 'c48-emulator',
                     'c48-v1-native', 'c48-v1-bytecode', 'lm-new-sdk',
                     'hanoi-queens8', 'gallery', 'fuse-independent-boot', 'release-copy'):
            self.assertIn("step('" + name + "'", text)
        self.assertIn('validate_boot_command(', text)
        self.assertIn('validate_boot_proof(', text)
        self.assertIn('check_tracked_sources(after_build=True)', text)
        self.assertIn("step('c48-coverage'", text)

    def test_nonempty_file_has_correct_sha256(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'report.txt'
            p.write_bytes(b'ZX UX test')
            self.assertEqual(release.validated_file(p), hashlib.sha256(b'ZX UX test').hexdigest())

    def test_missing_empty_and_link_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'content'
            with self.assertRaises(RuntimeError): release.validated_file(p)
            p.write_bytes(b'')
            with self.assertRaises(RuntimeError): release.validated_file(p)
            p.write_bytes(b'data')
            link = Path(d) / 'link'
            link.symlink_to(p)
            with self.assertRaises(RuntimeError): release.validated_file(link)

    def test_failing_local_command_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / 'failure.log'
            with patch.object(release, 'ROOT', Path(d)):
                with self.assertRaises(RuntimeError):
                    release.run([sys.executable, '-c', 'import sys; sys.exit(7)'],log=log)
            self.assertIn('Exit: 7', log.read_text())

    def test_tracked_source_hashes_are_mandatory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            p = root/'code.c';p.write_text('int x=1;\n')
            subprocess.run(['git', 'add', 'code.c'], cwd=root, check=True)
            with patch.object(release, 'ROOT', root):
                release.check_tracked_sources()
                p.write_text('int x=2;\n')
                with self.assertRaisesRegex(RuntimeError, 'Git index'):
                    release.check_tracked_sources()


if __name__ == '__main__': unittest.main()
