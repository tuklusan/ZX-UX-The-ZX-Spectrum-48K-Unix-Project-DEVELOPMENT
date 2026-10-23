"""Pin the historical tape's A=0 immediate glyph DATA proof."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from evolution_glyph_data import adapt_evolution_glyph_data
from test_evolution_tape_chain import tape_lines

TOKEN={0xf1:'LET',0xe5:'RESTORE',0xeb:'FOR',0xc0:'USR',0xcc:'TO',0xe3:'READ',0xf4:'POKE',0xf3:'NEXT',0xe4:'DATA',0xec:'GO TO',0xed:'GO SUB'}
class KW:
    TOKEN=TOKEN
class Source:
    @staticmethod
    def hide_numbers(raw,fp):return raw+b'\x0e\x00\x00\x00\x00\x00'
class Tap:
    @staticmethod
    def split_lines(rows):return list(rows)
    @staticmethod
    def join_lines(rows):return list(rows)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.original=tape_lines('44-evolution-1')
    def adapt(self,rows=None):return adapt_evolution_glyph_data(
        self.original if rows is None else rows,KW(),None,Source(),Tap())
    def test_four_literal_replacements_in_32_glyph_data(self):
        patched,proof=self.adapt()
        self.assertEqual(proof[0]['replaced_fields'],4)
        self.assertEqual(proof[0]['read_count'],32)
        self.assertEqual([n for n,b in self.original if dict(patched)[n]!=b],[1020,1030,1040])
        from evolution_glyph_data import _split_fields
        zero_count=sum(sum(field.startswith(b'0\x0e') for field in _split_fields(dict(patched)[n][1:-1]))
                       for n in [1020,1030,1040])
        self.assertEqual(zero_count,4)
    def test_unchanged_program_when_nonmatching(self):
        x=tape_lines('45-evolution-2');self.assertEqual(self.adapt(x),(x,[]))
    def test_initializer_change_rejected(self):
        x=[(n,b.replace(b'a=0\x0e',b'a=1\x0e') if n==1000 else b) for n,b in self.original]
        self.assertFalse(self.adapt(x)[1])
    def test_data_value_undefined_rejected(self):
        x=[(n,b.replace(b'a,24',b'z,24') if n==1020 else b) for n,b in self.original]
        self.assertFalse(self.adapt(x)[1])
    def test_extra_data_rejected(self):
        x=[(n,b.replace(b',73\x0e',b',73\x0e',1).replace(b'a,73',b'a,a,73') if n==1030 else b) for n,b in self.original]
        self.assertFalse(self.adapt(x)[1])
    def test_branch_into_data_rejected(self):
        self.assertFalse(self.adapt(self.original+[(999,b'\xec1020\x0e\x00\x00\xfc\x03\x00\r')])[1])
    def test_other_restore_rejected(self):
        self.assertFalse(self.adapt(self.original+[(999,b'\xe51020\x0e\x00\x00\xfc\x03\x00\r')])[1])
if __name__=='__main__':unittest.main()