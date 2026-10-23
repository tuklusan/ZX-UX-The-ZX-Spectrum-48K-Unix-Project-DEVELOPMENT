"""Verify unchanged Swordsman array content, address order and bounds."""
import hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from string_dim_flatten import adapt_flat_string_dims

class KW:
    CODE_FOR={'DIM':0xe9,'FOR':0xeb,'TO':0xcc,'LET':0xf1,
              'INT':0xba,'RND':0xa5,'IF':0xfa}
class Source:
    @staticmethod
    def hide_numbers(raw,fp):
        n=int(raw)
        return raw+b'\x0e\x00\x00'+n.to_bytes(2,'little')+b'\x00'
class Tap:
    def split_lines(self,p):
        if isinstance(p,list):return p
        result=[];i=0
        while i<len(p):
            line=int.from_bytes(p[i:i+2],'big')
            size=int.from_bytes(p[i+2:i+4],'little')
            result.append((line,p[i+4:i+4+size]));i+=4+size
        assert i==len(p)
        return result
    def join_lines(self,rows):return list(rows)
ROOT=Path(__file__).resolve().parents[3]/'src/bonus/60-programs/54-swordsman/BASIC/54-swordsman.tzx'
def original():
    b=ROOT.read_bytes()
    assert hashlib.sha256(b).hexdigest()=='11219d7b2501f67088946bee52155bf641b8515445b0302c2980c7b95185d4e4'
    assert b.startswith(b'ZXTape!\x1a')
    pos=10;blocks=[]
    while pos<len(b):
        assert b[pos]==0x10
        length=int.from_bytes(b[pos+3:pos+5],'little')
        blocks.append(b[pos+5:pos+5+length]);pos+=5+length
    return Tap().split_lines(blocks[1][1:-1])
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=original()
    def adapt(self,rows=None):
        return adapt_flat_string_dims(self.rows if rows is None else rows,KW(),None,Source(),Tap())
    def test_exact_original_tape(self):
        changed,proof=self.adapt()
        self.assertEqual(len(proof),1)
        self.assertEqual(proof[0]['array_shapes'],{'D$':[12,4],'M$':[108,5]})
        self.assertEqual([n for (n,b),(n2,a) in zip(changed,self.rows) if a!=b],
                         [500,510,660,4038,4060,4088])
    def test_flatten_addresses_are_bijective(self):
        d={(i-1)*3+j for i in range(1,5) for j in range(1,4)}
        m={(k-1)*12+(j-1)*3+i for k in range(1,10)
           for j in range(1,5) for i in range(1,4)}
        self.assertEqual(d,set(range(1,13)))
        self.assertEqual(m,set(range(1,109)))
        self.assertEqual(4*3*4,12*4)
        self.assertEqual(9*4*3*5,108*5)
    def test_changed_dimension_rejected(self):
        rows=[(n,b.replace(b'M$(9\x0e',b'M$(8\x0e') if n==500 else b)
              for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
    def test_changed_loop_bounds_rejected(self):
        rows=[(n,b.replace(b'9\x0e',b'8\x0e') if n==650 else b)
              for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
    def test_added_array_access_rejected(self):
        self.assertFalse(self.adapt(self.rows+[(4050,b'\xf5D$(1,1)\r')])[1])
    def test_changed_direction_writer_rejected(self):
        rows=[(n,b.replace(b'D7=4\x0e',b'D7=5\x0e') if n==4035 else b)
              for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
if __name__=='__main__': unittest.main()
