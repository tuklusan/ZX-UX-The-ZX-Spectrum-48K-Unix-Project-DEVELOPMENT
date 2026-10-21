#!/usr/bin/env python3
"""Check that successful builds replace dist without modifying source bonus."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / 'release/build/build.py'


class BonusRebuildChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = self.root / 'release'
        self.dist = self.release / 'dist'
        self.src = self.release / 'src'
        self.tools = self.src / 'zx-ux-sdk/tools'
        self.tools.mkdir(parents=True)
        kernel = self.src / 'zx-ux'
        (kernel / 'rom').mkdir(parents=True)
        (kernel / 'rom/48.rom').write_bytes(b'rom')
        (kernel / 'font4x8.bin').write_bytes(b'font')
        (self.release / 'build').mkdir()
        (self.dist / 'assets/c48-src').mkdir(parents=True)
        (self.dist / 'assets/c48-src/hello.c').write_bytes(b'int main(void) { return 0; }\n')
        (self.release / 'build/build.py').write_bytes(BUILD_SCRIPT.read_bytes())
        basic = self.src / 'bonus/60-programs/01-minelay/BASIC'
        (basic / 'SCREENSHOTS').mkdir(parents=True)
        (basic / '01-minelay.bas').write_bytes(b'10 PRINT "HELLO"\r\n')
        (basic / '01-minelay.tzx').write_bytes(b'\x00\xff\x01')
        (basic / 'SCREENSHOTS/01-INTRO.png').write_bytes(b'\x89PNG\r\n\x1a\n\0')
        (self.src / 'bonus/notes.txt').write_text('keep source untouched\n')
        (self.tools / 'osbuild.py').write_text('''
from pathlib import Path
R = Path(__file__).resolve().parents[3]
def mkfs(syms, programs): return None, None, 1024, None
def program_list(): return []
if __name__ == '__main__':
    (R / 'build/src/unix.sym').write_text('kend: EQU 0x7000\\n')
''')
        (self.tools / 'turbo_boot_build.py').write_text('''
from pathlib import Path
def create_tzx(*args, **kwargs):
    (Path(__file__).resolve().parents[3] / 'build/out/ZX-UX.tzx').write_bytes(b'tape')
''')
        (self.tools / 'c48build.py').write_text('''
def build(*args):
    args[2].mkdir(parents=True, exist_ok=True)
    (args[2] / 'compiled.bin').write_bytes(b'executable')
''')
        (self.tools / 'sdkpack.py').write_text('''
def pack(*args):
    args[-1].mkdir(parents=True, exist_ok=True)
    (args[-1] / 'rcc').write_text('sdk')
''')

    def rebuild(self, success=True):
        result = subprocess.run([sys.executable, '-B', str(self.release / 'build/build.py')],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)

    def snapshot(self, root):
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob('*') if p.is_file()}

    def test_repeated_rebuild_replaces_dist_and_copies_bonus(self):
        before = self.snapshot(self.src / 'bonus')
        (self.dist / 'stale.txt').write_text('remove')
        old_inode = self.dist.stat().st_ino
        self.rebuild()
        self.assertNotEqual(self.dist.stat().st_ino, old_inode)
        self.assertFalse((self.dist / 'stale.txt').exists())
        self.assertEqual(self.snapshot(self.dist / 'bonus'), before)
        self.assertEqual((self.dist / 'assets/c48-src/hello.c').read_bytes(),
                         b'int main(void) { return 0; }\n')
        self.assertEqual((self.dist / 'assets/c48-bin/compiled.bin').read_bytes(), b'executable')
        self.assertEqual((self.dist / 'zx-ux/ZX-UX.tzx').read_bytes(), b'tape')
        self.assertEqual((self.dist / 'sdk/bin/rcc').read_text(), 'sdk')
        (self.dist / 'stale-again.txt').write_text('remove again')
        self.rebuild()
        self.assertFalse((self.dist / 'stale-again.txt').exists())
        self.assertEqual(self.snapshot(self.dist / 'bonus'), before)
        self.assertEqual(self.snapshot(self.src / 'bonus'), before)
        self.assertFalse((self.src / 'bonus/60-programs/01-minelay/C48').exists())

    def test_failed_builder_preserves_previous_dist(self):
        before = self.snapshot(self.dist)
        (self.tools / 'c48build.py').write_text('def build(*args): raise RuntimeError("fail")\n')
        self.rebuild(success=False)
        self.assertEqual(self.snapshot(self.dist), before)
        self.assertFalse((self.release / 'build/dist-old').exists())

    def test_rejects_link_in_bonus_source(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'important').write_text('no changes')
        (self.src / 'bonus/link').symlink_to(outside, target_is_directory=True)
        self.rebuild(success=False)
        self.assertEqual((outside / 'important').read_text(), 'no changes')
        self.assertFalse((self.release / 'build/dist-new').exists())

    def test_rejects_linked_dist_root(self):
        (self.dist / 'assets/c48-src/hello.c').unlink()
        # The build must reject a linked dist root before any deletion.
        real = self.release / 'real-dist'
        self.dist.rename(real)
        self.dist.symlink_to(real, target_is_directory=True)
        self.rebuild(success=False)
        self.assertTrue(self.dist.is_symlink())
        self.assertTrue((real / 'assets/c48-src').is_dir())

    def test_rejects_linked_staging_directory(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'important').write_text('no changes')
        (self.release / 'build/dist-new').symlink_to(outside, target_is_directory=True)
        self.rebuild(success=False)
        self.assertEqual((outside / 'important').read_text(), 'no changes')


if __name__ == '__main__':
    unittest.main()
