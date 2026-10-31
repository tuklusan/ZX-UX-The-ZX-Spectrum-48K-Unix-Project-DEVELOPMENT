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
        (self.src / 'zx-ux/unix.asm').write_bytes(b'kernel source')
        (self.src / 'assets/forth-src').mkdir(parents=True)
        (self.src / 'assets/c48-src').mkdir(parents=True)
        (self.src / 'assets/c48-src/demo.c').write_text('void main(void) {}')
        (self.src / 'docs').mkdir()
        (self.src / 'docs/manual.txt').write_text('manual')
        bonus = self.src / 'bonus/60-programs'
        for number in range(1, 61):
            folder = bonus / f'{number:02d}-demo/BASIC'
            folder.mkdir(parents=True)
            (folder / 'demo.bas').write_text('10 PRINT "OK"')
        (bonus / 'sixty-programs-social-preview.png').write_bytes(b'preview')
        (self.root / 'LICENSE').write_text('project license')
        (self.root / 'THIRD-PARTY').write_text('third party')
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
        (tools / 'basicpack.py').write_text('def package(*args): return 1\n')
        (tools / 'rb2ctpack.py').write_text('def package(*args): return 3\n')
        (tools / 'pascalpack.py').write_text('def package(*args): return 1\n')
        (tools / 'fortranpack.py').write_text('def package(*args): return 1\n')
        (tools / 'forthbuild.py').write_text('''
def build(stage, sources, dest):
    dest.mkdir(parents=True)
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
        self.assertTrue((self.dist/'zx-ux/tzx/ZX-UX.tzx').is_file())
        self.assertEqual((self.dist/'docs/manual.txt').read_text(), 'manual')
        self.assertEqual((self.dist/'bonus/60-programs/01-demo/BASIC/demo.bas').read_text(), '10 PRINT "OK"')
        (self.dist/'stale').write_text('obsolete')
        self.run_builder()
        self.assertFalse((self.dist/'stale').exists())
        self.assertEqual((self.dist/'docs/manual.txt').read_text(), 'manual')
        self.assertEqual((self.src/'bonus/60-programs/01-demo/BASIC/demo.bas').read_text(), '10 PRINT "OK"')

    def test_bonus_has_only_numbered_programs_and_preview(self):
        source = self.src / 'bonus/60-programs'
        extras = ('CLEAN-INDEX.json', 'CLEANUP-SUMMARY.json', 'INDEX.csv',
                  'PROGRAMS.zip', 'README-FIRST.TXT', 'SHA256SUMS.txt')
        for name in extras:
            (source / name).write_text('historical source data')
        (source / 'TOOLS').mkdir()
        (source / 'TOOLS/helper.py').write_text('pass')
        (self.src / 'bonus/other-source.txt').write_text('not for release')
        self.run_builder()
        output = self.dist / 'bonus/60-programs'
        expected = {f'{number:02d}-demo' for number in range(1, 61)}
        expected.add('sixty-programs-social-preview.png')
        self.assertEqual({p.name for p in output.iterdir()}, expected)
        self.assertEqual({p.name for p in (self.dist / 'bonus').iterdir()},
                         {'60-programs'})
        self.assertEqual((output / 'sixty-programs-social-preview.png').read_bytes(),
                         b'preview')
        self.assertTrue((source / 'PROGRAMS.zip').exists())
        self.assertTrue((source / 'TOOLS/helper.py').exists())
        self.assertFalse((output/'c48lib').exists())
        self.run_builder()
        self.assertEqual({p.name for p in output.iterdir()}, expected)

    def test_historical_c48_port_is_not_copied_into_bonus(self):
        source = self.src / 'bonus/60-programs/01-demo/C48'
        source.mkdir()
        (source / 'main.c').write_text('old port')
        self.run_builder()
        self.assertFalse((self.dist / 'bonus/60-programs/01-demo/C48').exists())
        self.assertEqual((source / 'main.c').read_text(), 'old port')

    def test_existing_c48_gallery_survives_staged_rebuild(self):
        original = self.dist / 'screenshots/c48/rvm/games/arith.png'
        original.parent.mkdir(parents=True)
        original.write_bytes(b'existing RVM screenshot')
        self.run_builder()
        self.assertEqual(original.read_bytes(), b'existing RVM screenshot')

    def test_layout_and_license(self):
        self.run_builder()
        self.assertEqual((self.dist / 'zx-ux/tzx/ZX-UX.tzx').read_bytes(), b'tape')
        self.assertFalse((self.dist / 'zx-ux/ZX-UX.tzx').exists())
        self.assertEqual((self.dist / 'zx-ux/src/unix.asm').read_bytes(), b'kernel source')
        self.assertEqual((self.dist / 'zx-ux/src/rom/48.rom').read_bytes(), b'rom')
        self.assertEqual((self.dist / 'LICENSE').read_text(), 'project license')
        self.assertFalse((self.dist / 'sdk/bin/LICENSE').exists())
        self.assertFalse((self.dist / 'sdk/bin/THIRD-PARTY.txt').exists())
        self.assertEqual((self.dist / 'THIRD-PARTY').read_text(), 'third party')

    def test_missing_numbered_program_preserves_prior_dist(self):
        self.run_builder()
        target = self.dist / 'bonus/60-programs/01-demo/BASIC/demo.bas'
        before = target.read_bytes()
        folder = self.src / 'bonus/60-programs/60-demo'
        import shutil
        shutil.rmtree(folder)
        self.run_builder(ok=False)
        self.assertEqual(target.read_bytes(), before)

    def test_failure_preserves_dist(self):
        self.run_builder()
        before = (self.dist/'zx-ux/tzx/ZX-UX.tzx').read_bytes()
        docs_before = (self.dist/'docs/manual.txt').read_text()
        (self.src/'zx-ux-sdk/tools/c48build.py').write_text('def build(*a): raise RuntimeError("failed")\n')
        self.run_builder(ok=False)
        self.assertEqual((self.dist/'zx-ux/tzx/ZX-UX.tzx').read_bytes(), before)
        self.assertEqual((self.dist/'docs/manual.txt').read_text(), docs_before)

    def test_missing_docs_does_not_modify_previous_dist(self):
        self.run_builder()
        (self.src / 'docs/manual.txt').unlink()
        (self.src / 'docs').rmdir()
        self.run_builder(ok=False)
        self.assertEqual((self.dist/'docs/manual.txt').read_text(), 'manual')

    def test_docs_are_copied_after_sdk_pack(self):
        # The SDK pack is the last generator. A new doc written by it must
        # appear in the published distribution.
        pack = self.src / 'zx-ux-sdk/tools/sdkpack.py'
        pack.write_text(pack.read_text() +
                        "    (args[0].parent/'docs/late.txt').write_text('latest')\n")
        self.run_builder()
        self.assertEqual((self.dist/'docs/late.txt').read_text(), 'latest')

    def test_caches_are_not_distributed(self):
        for folder in (self.src/'docs', self.src/'bonus',
                       self.src/'assets/c48-src', self.src/'zx-ux-sdk'):
            cache = folder / '__pycache__'
            cache.mkdir()
            (cache / 'stale.pyc').write_bytes(b'ignored')
        self.run_builder()
        self.assertFalse(any(p.name == '__pycache__' or p.suffix == '.pyc'
                             for p in self.dist.rglob('*')))


if __name__ == '__main__':
    unittest.main()
