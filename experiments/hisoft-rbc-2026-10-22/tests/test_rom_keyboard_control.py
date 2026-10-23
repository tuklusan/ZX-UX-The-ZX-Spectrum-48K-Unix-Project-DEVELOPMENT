"""Bounded ROM keyboard control writes; arbitrary memory remains blocked."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from rom_keyboard_control import allow_rom_keyboard_controls
from dataclasses import dataclass


@dataclass
class Finding:
    operation: str
    classification: str
    severity: str
    expression: str


def guard(expr, operation='POKE', category='global_memory_write'):
    record = Finding(operation, category, 'block', expr)
    count = allow_rom_keyboard_controls([record])
    return count, record.severity, record.classification


class KeyboardControlTests(unittest.TestCase):
    def test_caps_mode_literal_values(self):
        for value in (0, 9, 10, 255):
            with self.subTest(value=value):
                self.assertEqual(guard(f'23658,{value}'),
                                 (1, 'info', 'rom_keyboard_control'))

    def test_key_click_literal_values(self):
        for value in (110, 111):
            self.assertEqual(guard(f'23609, {value}'),
                             (1, 'info', 'rom_keyboard_control'))

    def test_nearby_addresses_and_values_blocked(self):
        for expr in ('23659,255', '23657,255', '23608,111',
                     '23658,254', '23609,255', '23609,-1',
                     '23658,VAL x$', '23658+1,9', '23658,9+0',
                     '23606,0', '23672,255', '23692,255'):
            with self.subTest(expr=expr):
                self.assertEqual(guard(expr)[0], 0)

    def test_other_operations_blocked(self):
        self.assertEqual(guard('23658,255', operation='PEEK')[0], 0)
        self.assertEqual(guard('23658,255', category='rom_write')[0], 0)


if __name__ == '__main__':
    unittest.main()
