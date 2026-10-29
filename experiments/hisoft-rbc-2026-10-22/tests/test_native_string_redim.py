"""Test native repeated string DIM without modifying tokenized source."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from native_string_redim import _string_redims,with_string_redims
from native_redim_compiler import with_literal_redims
from z80asm import asm
from z80mini import Z80


def row(n,source):return (n,source.encode('latin1')+b'\r')

class Selection(unittest.TestCase):
    def test_repeated_two_dimensional_width_and_rows(self):
        rows=[row(10,'\xe9B$(2,6)'),row(20,'\xe9B$(2,4)'),row(30,'\xe9B$(2,2)')]
        self.assertEqual(_string_redims(rows),{1:((2,6),(2,4),(2,2))})
        self.assertEqual(_string_redims([row(10,'\xe9P$(4,3)'),row(20,'\xe9P$(2,3)')]),{15:((4,3),(2,3))})

    def test_no_false_positive_in_text_rem_data(self):
        rows=[row(10,'\xf5"\xe9A$(1,3)":\xea\xe9A$(1,2)'),
              row(20,'\xe4\xe9A$(1,5)'),row(30,'\xe9B$(3,5)')]
        self.assertEqual(_string_redims(rows),{})

    def test_dynamic_and_oversize_rejected(self):
        self.assertEqual(_string_redims([row(10,'\xe9B$(X,4)'),row(20,'\xe9B$(2,4)')]),{})
        self.assertEqual(_string_redims([row(10,'\xe9B$(500,200)'),row(20,'\xe9B$(2,3)')]),{})
        self.assertEqual(_string_redims([row(10,'\xe9B$(2,6)'),row(20,'\xe9B$(2,6)')]),{})

    def test_max_capacity_is_distinct_from_runtime_shape(self):
        class Base:
            def __init__(self):
                self.strvars=[dict(addr=1000,last=0,first=0,flags=0) for _ in range(26)]
                self.arrays=[dict(addr=0,last=0,first=0,type=0) for _ in range(26)]
                self.pass0=1;self.text=[]
            def reset(self,p):self.lines=p
            def _dim_sizes_set(self,ent,last,first):ent.update(last=last,first=first)
            def var_size(self,ent,t):return (ent['first'] or 1)*ent['last']
            def emit(self,s,*a):self.text.append(s.format(*a))
        cls=with_string_redims(with_literal_redims(Base,real_type=0,runtime_memfill=3),
                               string_type=0x80,memory_fill=3,element_rt=4)
        c=cls();c.reset([row(10,'\xe9B$(2,6)'),row(20,'\xe9B$(2,2)')])
        sv=c.strvars[1]
        c._dim_sizes_set(sv,6,2)
        c._dim_sizes_set(sv,2,2)
        self.assertEqual((sv['first'],sv['last']),(2,6))
        self.assertEqual(c.var_size(sv,0x80),14)
        self.assertEqual(sv['zxux_live_rows'],1014)

    def test_dim_loads_shape_as_immediate_not_relocated_address(self):
        # HiSoft ld_hl() is explicitly relocatable, even for small numbers.
        # Row widths/counts must use immediate Z80 instructions instead.
        class Base:
            def __init__(self):
                self.strvars=[{'addr':0x8010,'first':2,'last':6,
                               'zxux_live_rows':0x801e} for _ in range(26)]
                self._zxux_string_redims={1:((2,6),(2,4),(2,2))}
                self.events=[]
            def get_char(self):return ord('b')
            def peek_after(self):return ord('$')
            def next_char(self):return ord('$')
            def dim_sizes(self,ent):pass
            def emit(self,code,*args):self.events.append(('emit',code.format(*args)))
            def st_hl(self,addr):self.events.append(('store',addr))
            def ld_hl(self,addr):self.events.append(('reloc',addr))
            def ld_bc_abs(self,value):self.events.append(('count',value))
            def call_rt(self,rt):self.events.append(('runtime',rt))
        cls=with_string_redims(Base,string_type=0x80,memory_fill=3,element_rt=4)
        for rows,width in ((2,6),(2,4),(2,2),(4,3)):
            with self.subTest(rows=rows,width=width):
                instance=cls()
                instance._zxux_current_string_shape=(rows,width)
                instance.st_dim()
                self.assertEqual(instance.events[:4], [
                    ('emit',f'ld hl,{width}'),('store',0x8010),
                    ('emit',f'ld hl,{rows}'),('store',0x801e)])
                self.assertEqual([e for e in instance.events if e[0]=='reloc'],
                                 [('reloc',0x8012)])
                self.assertEqual(instance.events[-2:],
                                 [('emit','ld a,32'),('runtime',3)])

    def test_each_subscript_reads_current_rows_at_runtime(self):
        class Emitter:
            def __init__(self):self.assembly=[]
            def emit(self,text,*args):self.assembly.append(text.format(*args))
            def ld_hl_ind(self,addr):self.emit('ld hl,(${:04x})',addr)
        cls=with_string_redims(with_literal_redims(Emitter,real_type=0,runtime_memfill=3),
                               string_type=0x80,memory_fill=3,element_rt=4)
        x=cls();x._guard_index(0x8010)
        code=asm('; '.join(x.assembly)+'; ret')
        for rows,index,bad in [(2,2,False),(2,3,True),(4,3,False),(1,0,True)]:
            with self.subTest(rows=rows,index=index):
                data=bytearray(65536)
                data[0x8010:0x8012]=rows.to_bytes(2,'little')
                data[0x7000:0x7000+len(code)+3]=asm('ld hl,{}; '.format(index))+code
                cpu=Z80(data);cpu.sp=0x9000
                cpu.hooks[8]=lambda _: (_ for _ in ()).throw(IndexError('Subscript wrong'))
                if bad:
                    with self.assertRaises(IndexError):cpu.call(0x7000)
                else:
                    cpu.call(0x7000)
                    self.assertEqual(cpu.hl,index)
                self.assertEqual(data[0x8010:0x8012],rows.to_bytes(2,'little'))

if __name__=='__main__':unittest.main()
