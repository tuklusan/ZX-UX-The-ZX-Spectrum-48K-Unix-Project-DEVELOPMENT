"""Original Postman input bounds and rejection tests."""
import sys,hashlib,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from input_bound_dims import adapt_input_bound_dims
from test_redim_capacity import Tap,Source
TOKEN={0xeb:'FOR',0xcc:'TO',0xed:'GO SUB',0xec:'GO TO',0xee:'INPUT',0xfe:'RETURN',0xe9:'DIM',0xf1:'LET',0xfa:'IF',0xcb:'THEN',0xc5:'OR',0xa5:'RND',0xba:'INT',0xfb:'CLS'}
class KW:
    TOKEN=TOKEN
    CODE_FOR={v:k for k,v in TOKEN.items()}
ROOT=Path(__file__).resolve().parents[3]/'src/bonus/60-programs/36-postman/BASIC/36-postman.tzx'
def tape_program():
    b=ROOT.read_bytes()
    assert hashlib.sha256(b).hexdigest()=='af112fd1bbff766a07a8a2c4b3856e9dcc59af96bdd67f3f22db9a8bd68e1213'
    assert b.startswith(b'ZXTape!\x1a')
    pos=10;blocks=[]
    while pos<len(b):
        assert b[pos]==16
        size=int.from_bytes(b[pos+3:pos+5],'little')
        blocks.append(b[pos+5:pos+5+size]);pos+=5+size
    return Tap().split_lines(blocks[1][1:-1])
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=tape_program()
    def convert(self,rows=None):
        return adapt_input_bound_dims(self.rows if rows is None else rows,KW(),None,Source(),Tap())
    def test_original_tape_bounded_allocation(self):
        new,proof=self.convert()
        self.assertEqual(proof,[{'line':7060,'arrays':['y','x'],'capacity':36,'bound_line':5790}])
        before=dict(self.rows);after=dict(new)
        self.assertEqual([n for n in before if before[n]!=after[n]],[7060])
        self.assertTrue(after[7060].startswith(b'\xe9y(36\x0e'))
    def test_bounds_change_rejected(self):
        rows=[(n,b.replace(b'36\x0e',b'99\x0e') if n==5790 else b) for n,b in self.rows]
        self.assertFalse(self.convert(rows)[1])
    def test_new_input_writer_rejected(self):
        rows=self.rows+[(6000,b'\xee lb\r')]
        self.assertFalse(self.convert(rows)[1])
    def test_bypass_input_rejected(self):
        rows=[(n,b'\xed7000\r' if n==10 else b) for n,b in self.rows]
        self.assertFalse(self.convert(rows)[1])
    def test_out_of_range_access_rejected(self):
        rows=self.rows+[(6000,b'\xf1y(38)=1\r')]
        self.assertFalse(self.convert(rows)[1])
if __name__=='__main__':unittest.main()
