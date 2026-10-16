"""Independently exercise the rcc output-size admission gate.

The release toolchain must not emit a fresh executable when it rejects a
memory budget. A previously accepted output must remain byte-identical.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO

ROOT = pathlib.Path(__file__).resolve().parents[1]
SDK_SOURCE = ROOT / 'release/src/zx-ux-sdk'
SDK_STAGE = ROOT / 'release/build/tmp/sdk'
# Tests consume the freshly staged self-contained SDK, which includes the ROM.
if (SDK_STAGE / 'rcc/driver.py').read_bytes() != (SDK_SOURCE / 'rcc/driver.py').read_bytes():
    raise AssertionError('test requires a fresh, exact-source offline SDK staging')
sys.path.insert(0, str(SDK_STAGE))
from rcc import driver


class RccBudgetAdmission(unittest.TestCase):
    def test_overlimit_denies_output_without_erasing_prior_binary(self):
        source = ROOT / 'release/src/assets/c48-src/examples/hello.c'
        self.assertTrue(source.is_file(), source)
        with tempfile.TemporaryDirectory() as temp:
            target = pathlib.Path(temp) / 'hello.ssx'
            stderr = StringIO()
            with redirect_stderr(stderr):
                code = driver.main([str(source), '-o', str(target), '--max', '1'])
            self.assertNotEqual(code, 0, stderr.getvalue())
            self.assertFalse(target.exists(), 'rejected build wrote an executable')
            self.assertIn('needs', stderr.getvalue())
            self.assertIn('limit 1', stderr.getvalue())

            self.assertEqual(driver.main([str(source), '-o', str(target), '--max', '14000']), 0)
            good = target.read_bytes()
            self.assertTrue(good.startswith(b'SSX1'))
            with redirect_stderr(StringIO()):
                code = driver.main([str(source), '-o', str(target), '--max', '1'])
            self.assertNotEqual(code, 0)
            self.assertEqual(target.read_bytes(), good, 'rejected build changed last good output')

    def test_explicit_native_overlimit_also_denied(self):
        source = ROOT / 'release/src/assets/c48-src/examples/hello.c'
        with tempfile.TemporaryDirectory() as temp:
            target = pathlib.Path(temp) / 'hello-native.ssx'
            code = driver.main([str(source), '--native', '--max', '1', '-o', str(target)])
            self.assertNotEqual(code, 0)
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
