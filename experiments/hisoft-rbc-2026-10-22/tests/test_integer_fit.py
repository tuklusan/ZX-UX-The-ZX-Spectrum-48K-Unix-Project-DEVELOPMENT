import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage'))
from integer_fit import infer_integral_scalars

class K:
    TOKEN = {0xf1: 'LET', 0xeb: 'FOR', 0xcc:'TO', 0xcd:'STEP',
             0xf3:'NEXT', 0xf5:'PRINT', 0xf4:'POKE', 0xee:'INPUT',
             0xe3:'READ', 0xe9:'DIM'}

def check(rows):
    return infer_integral_scalars(None, K(), lambda _: [(i,s) for i,s in rows])

class Tests(unittest.TestCase):
    def test_literal_and_loop(self):
        self.assertEqual(check([(10,b'\xf1 a=12\r'),(20,b'\xeb b=1 \xcc 4\r')])[0],['INT a,b'])
    def test_unknown_write_disables_candidate(self):
        self.assertEqual(check([(10,b'\xf1 a=12\r'),(20,b'\xf1 a=b+1\r')])[0],[])
    def test_fractional_loop_is_not_narrowed(self):
        self.assertEqual(check([(10,b'\xeb b=1 \xcc 4 \xcd .5\r')])[0],[])
    def test_functional_input_disables(self):
        self.assertEqual(check([(10,b'\xf1 a=12\r'),(20,b'\xee a\r')])[0],[])
    def test_dynamic_poke_disables(self):
        self.assertEqual(check([(10,b'\xf1 a=12\r'),(20,b'\xf4 32000,0\r')])[0],[])
    def test_large_loop_would_overflow(self):
        self.assertEqual(check([(10,b'\xeb a=30000 \xcc 30000 \xcd 1\r')])[0],[])
    def test_array_reference_disables(self):
        self.assertEqual(check([(10,b'\xf1 a=12\r'),(20,b'\xf5 a(1)\r')])[0],[])
    def test_only_literal_in_quotes(self):
        self.assertEqual(check([(10,b'\xf1 a=12\r'),(20,b'\xf5 "POKE:\xf1 a=44"\r')])[0],['INT a'])
    def test_zero_headroom(self):
        self.assertEqual(infer_integral_scalars(None,K(),lambda _: [(10,b'\xf1 a=1\r')],0)[0],[])

if __name__=='__main__':
    unittest.main()
