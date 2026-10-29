"""Measure DIM budgets after the real INPUT bridge, without game exceptions."""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT/'src/zx-ux-sdk')]
import rld
from native_rbc_cli import compile_native

CHECKPOINT = Path(os.environ.get('RBC_TEST_CHECKPOINT', '/nonexistent'))
FRONTEND = Path(os.environ.get('RBC_TEST_FRONTEND', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_TEST_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT/'src/zx-ux-sdk/rom/48.rom'
READY = all(p.is_file() for p in (CHECKPOINT/'rbc.py', FRONTEND/'compiler.py', TAPE, ROM))


@unittest.skipUnless(READY, 'needs checked HiSoft compiler, tape and ROM')
class FinalNativeDimBudget(unittest.TestCase):
    def compile(self, src: Path):
        stderr = StringIO()
        with redirect_stderr(stderr):
            _, _, ssx, report = compile_native(src, CHECKPOINT, FRONTEND, TAPE, ROM)
        self.assertEqual(report['input_backend'], 'zxux')
        self.assertTrue(report['native_three_base_source_verified'])
        self.assertTrue(report['input_source_bridge_three_base_verified'])
        self.assertLessEqual(report['file'], 14000)
        self.assertLessEqual(report['total'], 14000)
        self.assertEqual(report['total'], len(rld.parse_ssx(ssx)['image']) +
                         report['bss'] + report['stack'])
        self.assertIn('RBC_WARN_DYNAMIC_DIM', stderr.getvalue())
        match = re.search(r'Reserved capacity per dimension: (\d+)', stderr.getvalue())
        self.assertIsNotNone(match)
        return ssx, report, int(match.group(1))

    def test_generic_numeric_dim_uses_final_native_input_cost(self):
        with TemporaryDirectory() as temp:
            src = Path(temp)/'numeric.bas'
            src.write_text('10 INPUT N\n20 DIM P(N)\n30 LET P(1)=N\n40 STOP\n',
                           encoding='ascii')
            _, report, capacity = self.compile(src)
            self.assertGreater(capacity, 1)
            # A numeric array reserves five bytes per live element. The next
            # element cannot fit if the final linked image was budgeted.
            self.assertGreater(report['total'] + 5, 14000)

    def test_original_independent_bas_and_tzx_match(self):
        folder = ROOT/'src/bonus/60-programs/51-anagrammatic'
        decoded = ROOT/'build/tmp/rbc-round2/51-anagrammatic/from-tape/51-anagrammatic.bas'
        if not decoded.is_file():
            self.skipTest('independently decoded tape source unavailable')
        a, ar, acap = self.compile(folder/'BASIC/51-anagrammatic.bas')
        b, br, bcap = self.compile(decoded)
        self.assertEqual(a, b)
        self.assertEqual(acap, bcap)
        self.assertEqual(ar['total'], br['total'])


if __name__ == '__main__':
    unittest.main()
