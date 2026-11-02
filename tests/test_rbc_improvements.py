"""Targeted original-Spectrum BASIC compatibility and safety regression checks."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
# Installed under repository tests/ (not on PYTHONPATH in the SDK).
SDK = ROOT / 'src/zx-ux-sdk'
sys.path[:0] = [str(SDK), str(SDK / 'rbc')]

from rbc.basic_listing import reconstruct_screen_wraps, encode_strict_listing
from rbc.native_run_rt import _run_entry, _RUN, _REM
from rbc.rom_keyboard_control import allow_rom_keyboard_controls
from rbc.spectrum_port254 import allow_port254, _TOKEN


class SinclairCompatibility(unittest.TestCase):
    def test_bare_run_skips_only_compiler_directives(self):
        directives = [
            (3, bytes((_REM, ord(':'))) + b' OPEN #'),
            (10, b'PRINT "START"\r'),
            (20, bytes((_RUN, 13))),
        ]
        self.assertEqual(_run_entry(directives, 0), 10)
        self.assertEqual(_run_entry(directives, 10), 10)
        self.assertEqual(_run_entry(directives, 11), 20)
        self.assertIsNone(_run_entry(directives, 21))

    def test_keyboard_repeat_literal_pairs_only(self):
        cases = [(23561, 35), (23561, 255), (23562, 5), (23562, 255),
                 (23658, 10), (23609, 110), (23561, 12), (23562, 16)]
        items = [SimpleNamespace(operation='POKE', classification='global_memory_write',
                                 severity='block', expression=f'{a},{v}') for a,v in cases]
        self.assertEqual(allow_rom_keyboard_controls(items), 6)
        self.assertEqual([x.severity for x in items[-2:]], ['block', 'block'])

    def test_ula_port_only_known_values(self):
        values = ['254,0', '254,16', '254,1', '254,A', '65534,16']
        items = [SimpleNamespace(operation='OUT', classification='raw_io_output',
                                 severity='block', expression=v) for v in values]
        self.assertEqual(allow_port254(items), 2)
        self.assertEqual([x.severity for x in items],
                         ['info', 'info', 'block', 'block', 'block'])
        self.assertIsNotNone(_TOKEN.match(b'254,16\r'))
        self.assertIsNone(_TOKEN.match(b'254,17\r'))

    def test_original_tape_wraps_reconstructed_without_source_edits(self):
        root = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing'
        for folder, name in [('12-morse-code', 'MorseCode.bas'),
                             ('13-nine-hole-golf', 'NineHoleGolf.bas')]:
            p = root / folder / 'BASIC' / name
            old = p.read_bytes()
            rebuilt = reconstruct_screen_wraps(old.decode('ascii'))
            self.assertLess(len(rebuilt.splitlines()), len(old.splitlines()))
            self.assertTrue(encode_strict_listing(rebuilt))
            self.assertEqual(p.read_bytes(), old)

    def test_well_formed_input_is_unchanged(self):
        text = '10 PRINT "HELLO"\n20 STOP\n'
        self.assertEqual(reconstruct_screen_wraps(text), text)
        with self.assertRaises(ValueError):
            reconstruct_screen_wraps('10 PRINT "HI"\ncontinuation-not-on-screen-width\n')


if __name__ == '__main__':
    unittest.main()
