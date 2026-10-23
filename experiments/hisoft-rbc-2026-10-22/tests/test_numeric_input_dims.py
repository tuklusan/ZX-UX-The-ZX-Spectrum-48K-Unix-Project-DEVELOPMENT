"""Verify guarded native player-array allocations on both preserved TZX tapes."""
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage'))
from numeric_input_dims import adapt_numeric_input_dims

TOKENS={0xe7:'BORDER',0xda:'PAPER',0xd9:'INK',0xe9:'DIM',0xf1:'LET',
        0xfa:'IF',0xcb:'THEN',0xba:'INT',0xa5:'RND',0xb1:'LEN',
        0xeb:'FOR',0xcc:'TO',0xcd:'STEP',0xf3:'NEXT',0xc1:'STR$',
        0xec:'GO TO',0xee:'INPUT',0xf5:'PRINT',0xfe:'RETURN',
        0xed:'GO SUB',0xc5:'OR',0xc7:'<=',0xc9:'<>',0xc8:'>=',
        0xfb:'CLS',0xad:'TAB',0xe2:'STOP'}
class KW:
    TOKEN=TOKENS
    CODE_FOR={v:k for k,v in TOKENS.items()}
class Tap:
    @staticmethod
    def split_lines(program):
        if isinstance(program,list):
            return list(program)
        rows=[];p=0
        while p<len(program):
            n=int.from_bytes(program[p:p+2],'big')
            size=int.from_bytes(program[p+2:p+4],'little')
            rows.append((n,program[p+4:p+4+size]));p+=4+size
        assert p==len(program)
        return rows
    @staticmethod
    def join_lines(rows):
        return list(rows)
class Source:
    @staticmethod
    def hide_numbers(b,fp):
        value=int(b)
        return b+b'\x0e\x00\x00'+value.to_bytes(2,'little')+b'\x00'
ROOT=Path(__file__).resolve().parents[3]/'src/bonus/60-programs'
SHA={
 '04-horse-race':'17e0fb5f040ca152f31954ccd1d34060af5ceca4fd21d0084aba0889d1276b72',
 '26-sheep-dog-trials':'8718bb6b4f886c8a4ce9459684cac6f0b66504d8a861bdb9559ad76938ab5e77',
}
def original_rows(name):
    data=(ROOT/name/'BASIC'/(name+'.tzx')).read_bytes()
    assert hashlib.sha256(data).hexdigest()==SHA[name]
    assert data.startswith(b'ZXTape!\x1a')
    pos=10;blocks=[]
    while pos<len(data):
        assert data[pos]==0x10
        n=int.from_bytes(data[pos+3:pos+5],'little')
        blocks.append(data[pos+5:pos+5+n]);pos+=5+n
    assert len(blocks)==2
    return Tap.split_lines(blocks[1][1:-1])

class TestNumericInputDims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={n:original_rows(n) for n in SHA}
    def adapt(self,name,rows=None):
        return adapt_numeric_input_dims(
            self.rows[name] if rows is None else rows,KW(),None,Source(),Tap())
    def test_horse_original_shape_and_guards(self):
        name='04-horse-race';new,proof=self.adapt(name)
        self.assertEqual(proof[0]['native_max_players'],128)
        self.assertEqual([n for n,b in self.rows[name] if dict(new)[n]!=b],[3,4,2030])
        self.assertEqual(dict(new)[4].count(b'128\x0e'),1)
        self.assertEqual(dict(new)[2030].count(b'128\x0e'),2)
        self.assertIn(bytes((KW.CODE_FOR['STOP'],)),dict(new)[3])
    def test_sheep_original_shape_and_guard(self):
        name='26-sheep-dog-trials';new,proof=self.adapt(name)
        self.assertEqual(proof[0]['native_max_players'],255)
        self.assertEqual([n for n,b in self.rows[name] if dict(new)[n]!=b],[30,40])
        self.assertEqual(dict(new)[40].count(b'255\x0e'),1)
        self.assertIn(bytes((KW.CODE_FOR['STOP'],)),dict(new)[30])
    def test_other_basic_remains_unmodified(self):
        rows=[(10,b'\xf5"HELLO"\r')]
        self.assertEqual(self.adapt('04-horse-race',rows),(rows,[]))
    def test_other_player_input_invalidates_horse(self):
        name='04-horse-race';rows=self.rows[name]+[(9100,b'\xee A\r')]
        self.assertFalse(self.adapt(name,rows)[1])
    def test_new_array_access_invalidates_horse(self):
        name='04-horse-race';rows=self.rows[name]+[(9100,b'\xf1 p(128)=1\r')]
        self.assertFalse(self.adapt(name,rows)[1])
    def test_input_changed_invalidates_sheep(self):
        name='26-sheep-dog-trials'
        rows=[(n,b.replace(b'A\r',b'B\r') if n==30 else b) for n,b in self.rows[name]]
        self.assertFalse(self.adapt(name,rows)[1])
    def test_large_new_access_invalidates_sheep(self):
        name='26-sheep-dog-trials';rows=self.rows[name]+[(6100,b'\xf1p(256)=1\r')]
        self.assertFalse(self.adapt(name,rows)[1])
    def test_dim_modified_invalidates_sheep(self):
        name='26-sheep-dog-trials'
        rows=[(n,b.replace(b'p(A)',b'p(99)') if n==40 else b) for n,b in self.rows[name]]
        self.assertFalse(self.adapt(name,rows)[1])
if __name__=='__main__':unittest.main()