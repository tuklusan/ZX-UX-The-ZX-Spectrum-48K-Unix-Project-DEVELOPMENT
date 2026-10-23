"""Original Spectrum tape and safety limits for fixed DATA expressions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from fixed_data import specialize_fixed_data
from constant_data import _separate

TOKENS={0xE3:'READ',0xE4:'DATA',0xE5:'RESTORE',0xE9:'DIM',0xEA:'REM',0xEB:'FOR',0xF1:'LET',0xF3:'NEXT',0xCC:'TO',0xEC:'GO TO',0xED:'GO SUB',0xFA:'IF',0xCB:'THEN',0xAA:'SCREEN$',0xD9:'AT',0xFE:'RETURN'}
class KW:
    TOKEN=TOKENS
class Tap:
    def split_lines(self,p):
        if isinstance(p,list):return p
        rows=[];pos=0
        while pos<len(p):
            n=int.from_bytes(p[pos:pos+2],'big');z=int.from_bytes(p[pos+2:pos+4],'little')
            rows.append((n,p[pos+4:pos+4+z]));pos+=z+4
        assert pos==len(p)
        return rows
    def join_lines(self,rows):return list(rows)
class Source:
    @staticmethod
    def hide_numbers(raw,fp):
        n=int(raw)
        return raw+b'\x0e\x00\x00'+n.to_bytes(2,'little')+b'\x00'

ROOT=Path(__file__).resolve().parents[1]/'src/bonus/60-programs/34-grand-prix/BASIC/34-grand-prix.tzx'
def read_tzx(p):
    raw=p.read_bytes(); assert raw.startswith(b'ZXTape!\x1a')
    pos=10; blocks=[]
    while pos<len(raw):
        assert raw[pos]==0x10
        n=int.from_bytes(raw[pos+3:pos+5],'little')
        blocks.append(raw[pos+5:pos+5+n]);pos+=5+n
    return blocks[1][1:-1]

class FixedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=Tap().split_lines(read_tzx(ROOT))
    def adapt(self,rows=None):return specialize_fixed_data(self.rows if rows is None else rows,KW(),None,Source(),Tap())
    def test_original_tape_exact_fields(self):
        new,proof=self.adapt()
        self.assertEqual(len(proof),1)
        self.assertEqual(proof[0]['fields'],26)
        self.assertEqual(proof[0]['fixed_fields'],21)
        old=dict(self.rows); out=dict(new)
        self.assertNotEqual(old[9400],out[9400])
        self.assertEqual([n for n in old if old[n]!=out[n]],[9400])
        fields=_separate(out[9400][1:-1])
        self.assertTrue(all(b'l' not in field.lower() for field in fields))
        self.assertEqual(len(fields),26)
        self.assertTrue(fields[0].startswith(b'-1\x0e'))
        self.assertTrue(fields[8].startswith(b'1\x0e'))
    def test_ambiguous_initializer_blocks(self):
        a=[(n,b'\xf1l=2\r' if n==9370 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(a)[1])
    def test_additional_write_blocks(self):
        a=[(n,b'\xf1l=5\r' if n==9529 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(a)[1])
    def test_incoming_jump_blocks(self):
        a=[(n,b'\xec9370\r' if n==9500 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(a)[1])
    def test_extra_restore_blocks(self):
        a=[(n,b'\xe59400\r' if n==9500 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(a)[1])
    def test_unknown_expression_blocks(self):
        a=[(n,b'\xe4l+1,l\r' if n==9400 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(a)[1])
    def test_wrong_data_count_blocks(self):
        a=[(n,b'\xe4l,l,7\r' if n==9400 else b) for n,b in self.rows]
        self.assertFalse(self.adapt(a)[1])

if __name__=='__main__':unittest.main()