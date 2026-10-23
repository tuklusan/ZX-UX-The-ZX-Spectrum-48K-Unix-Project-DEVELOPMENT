"""Read-only keyboard state must not expand memory write permissions."""
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from rom_keyread import allow_key_state_read

@dataclass
class Finding:
    line: int
    operation: str
    severity: str
    classification: str
    expression: str

class KeyStateReadTests(unittest.TestCase):
    def check(self,op,category,address):
        entry=Finding(10,op,'block',category,address)
        changed=allow_key_state_read([entry])
        return changed,entry.severity,entry.classification

    def test_exact_keyboard_state(self):
        self.assertEqual(self.check('PEEK','global_memory_read','23556'),
                         (1,'info','rom_keyboard_read'))
        self.assertEqual(self.check('PEEK','global_memory_read','23556=65 THEN'),
                         (1,'info','rom_keyboard_read'))

    def test_adjacent_address_is_not_supported(self):
        for expr in ('23557','23555','23556+1','23556-1','23556*2'):
            with self.subTest(expr=expr):
                self.assertEqual(self.check('PEEK','global_memory_read',expr)[0],0)

    def test_any_global_write_stays_blocked(self):
        self.assertEqual(self.check('POKE','global_memory_write','23556,65'),
                         (0,'block','global_memory_write'))

    def test_raw_machine_code_stays_blocked(self):
        self.assertEqual(self.check('USR','raw_machine_code_address','23556'),
                         (0,'block','raw_machine_code_address'))

if __name__=='__main__':
    unittest.main()