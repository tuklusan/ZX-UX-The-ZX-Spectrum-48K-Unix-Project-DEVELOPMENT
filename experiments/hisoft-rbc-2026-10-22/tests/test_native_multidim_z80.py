"""Execute each string-array axis bounds check on a real Z80 model."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_multidim_strings import with_multidim_strings
from z80asm import asm
from z80mini import Z80


class AxisSafety(unittest.TestCase):
    def test_rejects_zero_negative_and_upper_overflow_without_writes(self):
        class Collector:
            def __init__(self):self.code=[]
            def emit(self, text,*args):self.code.append(text.format(*args))
        cls=with_multidim_strings(Collector,string_type=0x80,multiply_rt=3,element_rt=2)
        compiler=cls()
        compiler._zxux_check_axis(5)
        code='; '.join(compiler.code)+'; ret'
        for index, bad in ((0,True),(1,False),(3,False),(5,False),(6,True),(65535,True)):
            with self.subTest(index=index):
                data=bytearray(65536)
                instructions=asm('ld hl,{}; '.format(index)+code)
                data[0x7000:0x7000+len(instructions)]=instructions
                data[0x8000:0x8008]=b'abcdefgh'
                cpu=Z80(data);cpu.sp=0x9000
                cpu.hooks[8]=lambda _: (_ for _ in ()).throw(IndexError('Subscript wrong'))
                if bad:
                    with self.assertRaises(IndexError):cpu.call(0x7000)
                else:
                    cpu.call(0x7000)
                    self.assertEqual(cpu.sp,0x9000)
                    self.assertEqual(cpu.hl,index)
                self.assertEqual(data[0x8000:0x8008],b'abcdefgh')

    def test_native_row_major_index_and_each_axis_bound(self):
        class Compiler:
            def __init__(self, dims, values):
                self.sv = {'zxux_dims': dims, 'addr': 0x8300}
                self.values = list(values)
                self.pos = 0
                self.ch = '('
                self.code = []
            def next_char(self):
                if self.ch not in '(),':
                    raise AssertionError('unexpected BASIC cursor')
                self.ch = 'index' if self.ch in '(,' else 'done'
            def get_char(self): return ord(self.ch)
            def expr_int(self):
                assert self.ch == 'index'
                val = self.values[self.pos]
                self.pos += 1
                self.emit('ld hl,{}',val)
                self.ch = ',' if self.pos < len(self.values) else ')'
            def emit(self, text, *args):self.code.append(text.format(*args))
            def ld_de(self, addr):self.emit('ld de,{}',addr)
            def call_rt(self, kind):self.emit('call ${:04x}',kind)
            def _strarr_tail(self):
                assert self.ch == ')'
            def not_supported(self,why):raise ValueError(why)
        cls = with_multidim_strings(Compiler, string_type=0x80,
                                     multiply_rt=0x7100, element_rt=0x7103)
        for dims, indices, expected in [
            ((4,3,4),(2,2),5),
            ((9,4,3,5),(9,4,3),108),
            ((9,4,3,5),(1,1,1),1),
            ((4,3,4),(0,2),None),
            ((4,3,4),(2,4),None),
            ((9,4,3,5),(9,4,4),None),
        ]:
            with self.subTest(dims=dims,indices=indices):
                c=cls(dims,indices)
                c.string_var_value(c.sv)
                self.assertEqual(c.pos,len(indices))
                data=bytearray(65536)
                code=asm('; '.join(c.code)+'; ret')
                data[0x6000:0x6000+len(code)]=code
                data[0x8300:0x8308]=b'abcdefgh'
                cpu=Z80(data);cpu.sp=0x9000
                called=[]
                cpu.hooks[8]=lambda _: (_ for _ in ()).throw(IndexError('Subscript wrong'))
                cpu.hooks[0x7100]=lambda z: setattr(z,'hl',(z.hl*z.de)&65535)
                cpu.hooks[0x7103]=lambda z: called.append((z.hl,z.de))
                if expected is None:
                    with self.assertRaises(IndexError):cpu.call(0x6000)
                    self.assertEqual(called,[])
                else:
                    cpu.call(0x6000)
                    self.assertEqual(called,[(expected,0x8300)])
                    self.assertEqual(cpu.sp,0x9000)
                self.assertEqual(data[0x8300:0x8308],b'abcdefgh')


if __name__=='__main__':unittest.main()
