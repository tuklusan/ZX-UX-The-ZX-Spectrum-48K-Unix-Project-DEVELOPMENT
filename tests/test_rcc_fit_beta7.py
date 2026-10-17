"""Opt-in bounded C48 compiler code-choice regressions.

All tests run against a freshly staged SDK produced by the offline builder.
No test assumes an absolute lower bound for the search result.
"""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'release/src/zx-ux-sdk'
STAGED = ROOT / 'release/build/sdk'
for name in ('rcc/driver.py', 'rcc/fit.py'):
    if (SOURCE / name).read_bytes() != (STAGED / name).read_bytes():
        raise AssertionError('offline SDK inputs are stale: ' + name)
sys.path.insert(0, str(STAGED))
from rcc import driver
from rcc.fit import find_smallest


class CompilerFitTest(unittest.TestCase):
    def test_fit_does_not_change_ordinary_default(self):
        source = str(ROOT / 'release/dist/assets/c48-src/examples/hello.c')
        with tempfile.TemporaryDirectory() as temp:
            a = Path(temp) / 'ordinary.ssx'
            b = Path(temp) / 'fit.ssx'
            self.assertEqual(driver.main([source, '-o', str(a)]), 0)
            self.assertEqual(driver.main([source, '-o', str(b), '--fit']), 0)
            self.assertTrue(a.read_bytes().startswith(b'SSX1'))
            self.assertTrue(b.read_bytes().startswith(b'SSX1'))
            self.assertEqual(driver.main([source, '-o', str(a)]), 0)

    def test_fit_deterministic_and_never_worse_than_endpoint_modes(self):
        source = str(ROOT / 'release/dist/assets/c48-src/demos/queens8.c')
        opts = {'heap': 1024, 'stack': 448, 'udgs': 32}
        native = driver.build(source, opts)
        bytecode = driver.build(source, dict(opts, bytecode='all'))
        best, count, modes = find_smallest(source, opts, driver.build)
        self.assertLessEqual(best[4], min(native[4], bytecode[4]))
        self.assertGreaterEqual(count, 2)
        self.assertLessEqual(count, 128)
        with tempfile.TemporaryDirectory() as temp:
            first, second = (Path(temp) / s for s in ('first.ssx', 'second.ssx'))
            for target in (first, second):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(driver.main([source, '--fit', '--stack', '448',
                                                  '--udgs', '32', '-o', str(target)]), 0)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.read_bytes(), best[0])

    def test_overbudget_denied_without_emitting_file(self):
        source = str(ROOT / 'release/dist/assets/c48-src/examples/hello.c')
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'no.ssx'
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                code = driver.main([source, '--fit', '--max', '1', '-o', str(target)])
            self.assertNotEqual(code, 0)
            self.assertIn('limit 1', errors.getvalue())
            self.assertFalse(target.exists())

    def test_recursive_auto_stack_is_not_declared_safe(self):
        source = str(ROOT / 'release/dist/assets/c48-src/demos/hanoi.c')
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'no.ssx'
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                code = driver.main([source, '--fit', '-o', str(target)])
            self.assertNotEqual(code, 0)
            self.assertIn('requires an explicit --stack', errors.getvalue())
            self.assertFalse(target.exists())

    def test_fit_flags_do_not_override_user_backend_or_mode(self):
        source = str(ROOT / 'release/dist/assets/c48-src/examples/hello.c')
        for flag in ('--native', '--bytecode', '-S', '-c'):
            with tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / 'no.ssx'
                with contextlib.redirect_stderr(io.StringIO()):
                    code = driver.main([source, '--fit', flag, '-o', str(target)])
                self.assertEqual(code, 2)
                self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
