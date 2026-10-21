"""Ordinary RCC builds must produce loadable, measured C48 executables.

This checks the same source-only SDK used for the release, with no per-demo
flags or duplicate multitasking sources.  The five live-pair checks live in
test_c48_pairings.py and run against freshly generated dist/SSX images.
"""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
from rcc import driver


class DefaultFit(unittest.TestCase):
    def source(self, name):
        return ROOT / 'src/assets/c48-src/demos' / (name + '.c')

    def test_default_demo_sizes_and_storage(self):
        # These values are inferred from recursion/glyph bounds, not from a
        # switch on source filename or a release-builder special case.
        for name, stack, maximum in (
            ('hanoi', 400, 5200),
            ('queens8', 416, 5300),
            ('mobius', 528, 5100),
            ('torus', 480, 5100),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / (name + '.ssx')
                self.assertEqual(driver.main([str(self.source(name)), '-o', str(out)]), 0)
                image = out.read_bytes()
                h = rld.parse_ssx(image)
                need = max(len(h['image']) + h['bss'] + h['stack'], len(image))
                self.assertGreaterEqual(h['stack'], 384)
                self.assertLessEqual(h['stack'], stack)
                self.assertLess(need, maximum)
                self.assertEqual(image, (ROOT / 'dist/assets/c48-bin/ssx' / out.name).read_bytes())

    def test_explicit_fit_matches_automatic_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('hanoi', 'queens8'):
                source = str(self.source(name))
                ordinary = Path(tmp) / (name + '-default.ssx')
                explicit = Path(tmp) / (name + '-fit.ssx')
                self.assertEqual(driver.main([source, '-o', str(ordinary)]), 0)
                self.assertEqual(driver.main([source, '-o', str(explicit), '--fit']), 0)
                self.assertEqual(ordinary.read_bytes(), explicit.read_bytes())

    def test_companion_assembly_is_linked_by_rcc(self):
        with tempfile.TemporaryDirectory() as tmp:
            for category, name in (('demos', 'ball'), ('games', 'invaders')):
                source = ROOT / 'src/assets/c48-src' / category / (name + '.c')
                self.assertTrue(source.with_suffix('.asm').is_file())
                ordinary = Path(tmp) / (name + '.ssx')
                self.assertEqual(driver.main([str(source), '-o', str(ordinary)]), 0)
                self.assertGreaterEqual(rld.parse_ssx(ordinary.read_bytes())['stack'], 800)
                self.assertEqual(ordinary.read_bytes(),
                                 (ROOT / 'dist/assets/c48-bin/ssx' / ordinary.name).read_bytes())

    def test_limit_rejects_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'too-big.ssx'
            with contextlib.redirect_stderr(io.StringIO()):
                result = driver.main([str(self.source('hanoi')), '-o', str(out), '--max', '1'])
            self.assertNotEqual(result, 0)
            self.assertFalse(out.exists())

    def test_explicit_backend_and_storage_still_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ('--bytecode', '--native'):
                out = Path(tmp) / (mode + '.ssx')
                args = [str(self.source('hanoi')), '-o', str(out), mode,
                        '--stack', '448', '--udgs', '32', '--max', '20000']
                self.assertEqual(driver.main(args), 0)
                self.assertEqual(rld.parse_ssx(out.read_bytes())['stack'], 448)


if __name__ == '__main__':
    unittest.main()
