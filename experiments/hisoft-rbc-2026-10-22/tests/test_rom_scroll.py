"""ROM scroll exception cannot admit a general machine-code jump."""
import sys
import unittest
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage'))
from rom_scroll import allow_rom_screen_scroll


@dataclass
class Check:
    operation: str = 'USR'
    classification: str = 'raw_machine_code_address'
    severity: str = 'block'
    expression: str = '3280'


class Tests(unittest.TestCase):
    def test_exact_rom_entry(self):
        finding = Check()
        self.assertEqual(allow_rom_screen_scroll([finding]), 1)
        self.assertEqual((finding.classification, finding.severity),
                         ('rom_screen_scroll', 'info'))

    def test_other_addresses_remain_blocked(self):
        for expr in ('3281', '3279', '0x0cd0', '3280+1', '3280*1',
                     'usr 3280', '3280 OR 0', 'c', '23658', '-3280'):
            with self.subTest(expr=expr):
                x = Check(expression=expr)
                self.assertEqual(allow_rom_screen_scroll([x]), 0)
                self.assertEqual(x.severity, 'block')

    def test_other_operations_remain_blocked(self):
        for op in ('PEEK', 'POKE', 'OUT', 'LOAD'):
            with self.subTest(op=op):
                x = Check(operation=op)
                self.assertEqual(allow_rom_screen_scroll([x]), 0)
                self.assertEqual(x.severity, 'block')

    def test_other_categories_remain_blocked(self):
        for category in ('global_memory_read', 'global_memory_write',
                         'tape_or_external_io', 'unbounded_memory_write'):
            x = Check(classification=category)
            self.assertEqual(allow_rom_screen_scroll([x]), 0)
            self.assertEqual(x.severity, 'block')

    def test_already_accepted_not_counted_twice(self):
        x = Check(severity='info')
        self.assertEqual(allow_rom_screen_scroll([x]), 0)


if __name__ == '__main__':
    unittest.main()