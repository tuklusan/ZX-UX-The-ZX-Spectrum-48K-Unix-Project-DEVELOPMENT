#!/usr/bin/env python3
"""Test fresh build and failure recovery without requiring an assembler."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / 'build.py'


class RebuildChecks(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name) / 'unpacked in a new location'
        self.src = self.root / 'src'
        self.dist = self.root / 'dist'
        tools = self.src / 'zx-ux-sdk/tools'
        tools.mkdir(parents=True)
        (self.src / 'zx-ux/rom').mkdir(parents=True)
        (self.src / 'zx-ux/rom/48.rom').write_bytes(b'rom')
        (self.src / 'zx-ux/font4x8.bin').write_bytes(b'font')
        (self.src / 'assets/c48-src').mkdir(parents=True)
        (self.src / 'assets/c48-src/demo.c').write_text('void main(void) {}')
        (self.src / 'bonus/60-programs/demo/BASIC').mkdir(parents=True)
        (self.src / 'bonus/60-programs/demo/BASIC/demo.bas').write_text('10 PRINT "OK"')
        (self.root / 'build').mkdir()
        (self.root / 'build/build.py').write_bytes(BUILD.read_bytes())
        (tools / 'osbuild.py').write_text('''
from pathlib import Path
R = Path(__file__).resolve().parents[3]
def mkfs(*args): return None, None, 1024, None
def program_list(): return []
if __name__ == '__main__':
    (R/'build/src/unix.sym').write_text('kend: EQU 0x7000\\n')
''')
        (tools / 'turbo_boot_build.py').write_text('''
from pathlib import Path
def create_tzx(*args, **kwargs):
    (Path(__file__).resolve().parents[3]/'build/out/ZX-UX.tzx').write_bytes(b'tape')
''')
        (tools / 'c48build.py').write_text('''
def build(stage, sources, dest):
    dest.mkdir(parents=True)
    (dest/'demo.ssx').write_bytes(b'code')
''')
        (tools / 'sdkpack.py').write_text('''
def pack(*args):
    args[-1].mkdir(parents=True)
    (args[-1]/'rcc').write_text('sdk')
''')

    def run_builder(self, ok=True):
        result = subprocess.run([sys.executable, '-B', str(self.root/'build/build.py')],
                                cwd=self.work.name, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)

    def test_cold_and_repeated_build(self):
        self.assertFalse(self.dist.exists())
        self.run_builder()
        self.assertTrue((self.dist/'zx-ux/ZX-UX.tzx').is_file())
        self.assertEqual((self.dist/'bonus/60-programs/demo/BASIC/demo.bas').read_text(), '10 PRINT "OK"')
        (self.dist/'stale').write_text('obsolete')
        self.run_builder()
        self.assertFalse((self.dist/'stale').exists())
        self.assertEqual((self.src/'bonus/60-programs/demo/BASIC/demo.bas').read_text(), '10 PRINT "OK"')

    def test_failure_preserves_dist(self):
        self.run_builder()
        before = (self.dist/'zx-ux/ZX-UX.tzx').read_bytes()
        (self.src/'zx-ux-sdk/tools/c48build.py').write_text('def build(*a): raise RuntimeError("failed")\n')
        self.run_builder(ok=False)
        self.assertEqual((self.dist/'zx-ux/ZX-UX.tzx').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
