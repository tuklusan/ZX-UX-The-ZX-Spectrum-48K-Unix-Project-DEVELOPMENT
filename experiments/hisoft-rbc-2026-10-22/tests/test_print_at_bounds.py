"""Strict RBC: provable invalid PRINT AT coordinates fail before code generation."""
from __future__ import annotations

from pathlib import Path
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'))
from basic_listing import encode_strict_listing
from native_rbc_cli import compile_native


class NativePrintAtRange(unittest.TestCase):
    def check_rejected(self, text, fragment):
        with self.assertRaisesRegex(ValueError, 'RBC E_PRINT_AT_RANGE: Line 10: ' + fragment):
            encode_strict_listing('10 ' + text + '\n')

    def test_rom_row_22_and_32_are_invalid(self):
        self.check_rejected('PRINT AT 22,0;"X"', 'PRINT AT row 22 outside 0..21')
        self.check_rejected('PRINT AT 32,13;"X"', 'PRINT AT row 32 outside 0..21')
        self.check_rejected('PRINT AT 255,7;"X"', 'PRINT AT row 255 outside 0..21')
        self.check_rejected('PRINT AT -1,7;"X"', 'PRINT AT row -1 outside 0..21')

    def test_column_32_and_255_are_invalid(self):
        self.check_rejected('PRINT AT 6,32;"X"', 'PRINT AT column 32 outside 0..31')
        self.check_rejected('PRINT INK 3;AT 6,255;"X"', 'PRINT AT column 255 outside 0..31')
        self.check_rejected('PRINT AT R,255;"X"', 'PRINT AT column 255 outside 0..31')

    def test_multiple_controls_and_constant_arithmetic(self):
        self.check_rejected('PRINT AT 2,3;AT 22,6;"X"', 'PRINT AT row 22 outside 0..21')
        self.check_rejected('IF A=1 THEN PRINT AT (21+1),0;"X"',
                            'PRINT AT row 22 outside 0..21')
        self.check_rejected('PRINT AT 4,30+2;"X"', 'PRINT AT column 32 outside 0..31')

    def test_valid_edges_and_runtime_unknowns_are_retained(self):
        for text in ('PRINT AT 0,0;"X"', 'PRINT AT 21,31;"X"',
                     'PRINT INK 1;PAPER 2;AT 10,0;"X"',
                     'PRINT AT Q(1),Q(2);"X"', 'PRINT AT ROW,COL;"X"',
                     'PRINT AT ROW,31;"X"',
                     'PRINT "AT 32,13"',
                     'REM PRINT AT 32,13',
                     'DATA 32,13: PRINT AT 10,5;"X"'):
            with self.subTest(text=text):
                self.assertTrue(encode_strict_listing('10 ' + text + '\n'))

    def test_inert_rem_and_string_data_cannot_cause_rejection(self):
        self.assertTrue(encode_strict_listing('10 PRINT "PRINT AT 255,7"\n'))
        self.assertTrue(encode_strict_listing('10 PRINT "A": REM PRINT AT 32,13\n'))
        self.assertTrue(encode_strict_listing('10 DATA 32,13: PRINT AT 21,31;"X"\n'))

    def test_production_cli_checks_before_invoking_recovered_compiler(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            checkpoint = work / 'rbc'
            frontend = work / 'frontend'
            checkpoint.mkdir()
            frontend.mkdir()
            (checkpoint / 'rbc.py').write_text('raise RuntimeError("must not load compiler")\n')
            (checkpoint / 'font32.bin').write_bytes(b'\x00' * 768)
            (frontend / 'compiler.py').write_text('\n')
            tape = work / 'compiler.tzx'
            tape.write_bytes(b'x')
            bad = work / 'bad.bas'
            bad.write_text('10 PRINT AT 32,13;"X"\n')
            with self.assertRaisesRegex(ValueError, 'E_PRINT_AT_RANGE: Line 10'):
                compile_native(bad, checkpoint, frontend, tape,
                               ROOT / 'src/zx-ux-sdk/rom/48.rom')

    def test_original_published_60_bas_sources_remain_tokenizable(self):
        originals = sorted((ROOT / 'src/bonus/60-programs').glob('*/BASIC/*.bas'))
        self.assertEqual(len(originals), 60)
        for path in originals:
            with self.subTest(game=path.parent.parent.name):
                self.assertTrue(encode_strict_listing(path.read_text(encoding='ascii')))


if __name__ == '__main__':
    unittest.main()
