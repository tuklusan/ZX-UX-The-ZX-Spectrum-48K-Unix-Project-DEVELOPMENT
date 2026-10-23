import sys, unittest, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from redim_capacity import adapt_bounded_redim

TOKEN={0xe7:'BORDER',0xda:'PAPER',0xd9:'INK',0xe9:'DIM',0xf1:'LET',0xfa:'IF',0xcb:'THEN',0xba:'INT',0xa5:'RND',0xb1:'LEN',0xeb:'FOR',0xcc:'TO',0xcd:'STEP',0xf3:'NEXT',0xc1:'STR$',0xec:'GO TO'}
class Kw:
    TOKEN=TOKEN
    CODE_FOR={v:k for k,v in TOKEN.items()}
class Tap:
    def split_lines(self,program):
        if isinstance(program,list):return list(program)
        out=[];i=0
        while i<len(program):
            n=int.from_bytes(program[i:i+2],'big')
            length=int.from_bytes(program[i+2:i+4],'little')
            out.append((n,program[i+4:i+4+length]));i+=4+length
        assert i==len(program)
        return out
    def join_lines(self,rows):return list(rows)
class Source:
    @staticmethod
    def hide_numbers(raw,fp):
        n=int(raw)
        return raw+b'\x0e\x00\x00'+n.to_bytes(2,'little')+b'\x00'
ROOT=Path(__file__).resolve().parents[3]/'src/bonus/60-programs/40-wordsum/BASIC/40-wordsum.tzx'
def tape_program():
    b=ROOT.read_bytes();assert b.startswith(b'ZXTape!\x1a')
    assert hashlib.sha256(b).hexdigest()=='24785370588cd89208b511ce16bc244be5fb8a1c82f9cb02cd3c50319d32043a'
    pos=10;blocks=[]
    while pos<len(b):
        assert b[pos]==16
        length=int.from_bytes(b[pos+3:pos+5],'little')
        blocks.append(b[pos+5:pos+5+length]);pos+=5+length
    return blocks[1][1:-1]

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=Tap().split_lines(tape_program())
    def run_rewrite(self,rows=None):return adapt_bounded_redim(self.rows if rows is None else rows,Kw(),None,Source(),Tap())
    def test_original_tape_rewrites_only_second_dim(self):
        updated,proof=self.run_rewrite()
        self.assertEqual(proof,[{'line':586,'array':'C','initial_capacity':10,'observed_capacity':6}])
        before=dict(self.rows); after=dict(updated)
        self.assertEqual([k for k in before if before[k]!=after[k]],[586])
        self.assertEqual(after[586].split(bytes((0xe9,)),1)[1][:9],b'C(10\x0e\x00\x00\x0a\x00')
        self.assertEqual(after[586].split(bytes((0xec,)),1)[1],before[586].split(bytes((0xec,)),1)[1])
    def test_extra_array_access_is_rejected(self):
        rows=self.rows+[(587,b'\xf1C(7\x0e\x00\x00\x07\x00\x00)=0\r')]
        self.assertFalse(self.run_rewrite(rows)[1])
    def test_longer_digit_source_is_rejected(self):
        rows=[(n,b.replace(b'\xa5*10\x0e',b'\xa5*99\x0e') if n==140 else b) for n,b in self.rows]
        self.assertFalse(self.run_rewrite(rows)[1])
    def test_missing_reset_is_rejected(self):
        rows=[(n,b'\xe9C(5\x0e\x00\x00\x05\x00\x00):\xec80\x0e\x00\x00P\x00\x00\r' if n==586 else b) for n,b in self.rows]
        self.assertFalse(self.run_rewrite(rows)[1])
    def test_unsupported_variable_write_is_rejected(self):
        rows=self.rows+[(245,b'\xf1T=10000000\r')]
        self.assertFalse(self.run_rewrite(rows)[1])
if __name__=='__main__':unittest.main()
