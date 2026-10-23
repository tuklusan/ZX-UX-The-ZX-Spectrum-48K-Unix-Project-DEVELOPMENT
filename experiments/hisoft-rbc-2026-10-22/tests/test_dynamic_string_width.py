"""Original sprite widths, byte parity and runtime layout tests."""
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from dynamic_string_width import _proven_layout, install

ROOT = Path(__file__).resolve().parents[3]
TZX = ROOT / 'src/bonus/60-programs/03-tug-of-war/BASIC/03-tug-of-war.tzx'
DIGEST = '10c4a2cffbdfec0e6917a4a7ecd311e01a074f61c297b35ca29053d7bbcfdea4'


def rows():
    b = TZX.read_bytes()
    assert hashlib.sha256(b).hexdigest() == DIGEST
    assert b.startswith(b'ZXTape!\x1a')
    pos = 10
    blocks = []
    while pos < len(b):
        assert b[pos] == 16
        length = int.from_bytes(b[pos+3:pos+5], 'little')
        blocks.append(b[pos+5:pos+5+length])
        pos += length + 5
    body = blocks[1][1:-1]
    result = []
    pos = 0
    while pos < len(body):
        number = int.from_bytes(body[pos:pos+2], 'big')
        n = int.from_bytes(body[pos+2:pos+4], 'little')
        result.append((number, body[pos+4:pos+4+n]))
        pos += 4 + n
    assert pos == len(body)
    return result


class Fixture:
    def __init__(self):
        self.strvars = [{'first':0,'last':0,'flags':0,'addr':400+i*24} for i in range(26)]
        self.buf = bytearray(b'a$(2,4)\r')
        self.ch = 0
        self.line_no = 4230
        self.t = None
        self.ops = []
        self._zxux_width_dim = True
    def get_char(self): return self.buf[self.ch]
    def next_char(self):
        self.ch += 1
        return self.buf[self.ch]
    def reset(self, prog): self.lines = prog
    def _dim_sizes_set(self, ent, last, first):
        if ent['last'] and ent['last']!=last:
            raise ValueError('unsupported different sizes')
        ent['first']=first
        ent['last']=last
    def dim_sizes(self, ent):
        self._dim_sizes_set(ent,4,2)
    def st_dim(self):
        raise AssertionError('should use runtime width')
    def string_var_value(self,sv):
        raise AssertionError('should use runtime element locator')
    def expr_int(self): self.ops.append(('expr',))
    def ld_de(self,n): self.ops.append(('de',n))
    def _strarr_tail(self): self.ops.append(('tail',))
    def emit(self,code,*args): self.ops.append(('asm',code,args))
    def st_hl(self,n): self.ops.append(('store',n))
    def ld_hl(self,n): self.ops.append(('hl',n))
    def ld_bc_abs(self,n): self.ops.append(('bc',n))
    def call_rt(self,n): self.ops.append(('rt',n))

class Module:
    Compiler = Fixture
    STRING = 3
    class RT:
        MEM_FILL = 20
        STR_ARR_ELEM = 21
    @staticmethod
    def letter(c): return ord(chr(c).lower())-97


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines=rows()
        install(Module)

    def test_actual_tape_uses_bounded_array_lengths(self):
        self.assertTrue(_proven_layout(self.lines))

    def test_unexpected_redefinition_fails(self):
        changed=[(n,b.replace(b'2\x0e\x00\x00\x02\x00\x00)',b'8\x0e\x00\x00\x08\x00\x00)')) if n==2232 else (n,b)
                 for n,b in self.lines]
        self.assertFalse(_proven_layout(changed))
        self.assertFalse(_proven_layout(self.lines+[(8000,b'\xe9a$(2,9)\r')]))

    def test_runtime_width_is_four_but_allocated_capacity_is_six(self):
        obj=Fixture()
        obj.st_dim()
        self.assertEqual((obj.strvars[0]['first'],obj.strvars[0]['last']),(2,6))
        self.assertEqual(obj.ops,[('asm','ld hl,{}',(4,)),('store',400),
                                  ('hl',402),('bc',7),('asm','ld a,32',()),('rt',20)])

    def test_index_both_literally_and_dynamically_uses_runtime_header(self):
        obj=Fixture()
        obj.strvars[0]['first']=2
        obj.strvars[0]['last']=6
        obj.buf=bytearray(b'(1)\r')
        obj.ch=0
        obj.string_var_value(obj.strvars[0])
        self.assertEqual(obj.ops,[('expr',),('de',400),('rt',21),('tail',)])

    def test_unchanged_other_programs_use_original_compiler(self):
        obj=Fixture()
        obj._zxux_width_dim=False
        with self.assertRaisesRegex(AssertionError,'should use runtime'):
            obj.st_dim()

    def test_install_is_idempotent(self):
        before=Module.Compiler.st_dim
        install(Module)
        self.assertIs(before,Module.Compiler.st_dim)

if __name__=='__main__': unittest.main()
