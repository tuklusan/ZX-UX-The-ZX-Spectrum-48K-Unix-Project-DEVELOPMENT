"""General literal redimensioning: source inspection, capacity and bounds."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_redim_compiler import _executable_dims, with_literal_redims


def row(n, text):
    return n, text.encode('latin1') + b'\r'


class SourceSelection(unittest.TestCase):
    def test_repeated_numeric_literals(self):
        lines = [row(10, '\xe9C(10\x0e\x00\x00\x0a\x00\x00)'),
                 row(20, '\xe9C(6\x0e\x00\x00\x06\x00\x00)')]
        self.assertEqual(_executable_dims(lines), {2:(10, 6)})

    def test_no_game_names_or_single_dimensions(self):
        self.assertEqual(_executable_dims([row(10,'\xe9A(3)'),row(20,'\xe9A(2)'),
                                           row(30,'\xe9B(5)')]),{0:(3,2)})

    def test_data_field_is_not_executable_dim(self):
        self.assertEqual(_executable_dims([row(10,'\xe4\xe9A(4):\xe9A(2)')]),{})

    def test_dynamic_or_multidimensional_shape_is_not_approved(self):
        self.assertEqual(_executable_dims([row(10,'\xe9A(3)'),row(20,'\xe9A(K)')]),{})
        self.assertEqual(_executable_dims([row(10,'\xe9A(3)'),row(20,'\xe9A(2,4)')]),{})

    def test_quoted_dim_and_rem_do_not_count(self):
        self.assertEqual(_executable_dims([row(10,'"\xe9A(4)":\xea\xe9A(3)'),
                                           row(20,'\xe9A(2)')]),{})


class Emission(unittest.TestCase):
    def test_runtime_shape_and_guards(self):
        class Base:
            def __init__(self):
                self.arrays=[dict(addr=100,last=0,first=0,type=0) for _ in range(26)]
                self.pass0=1; self.t=None; self.buf=b''; self.pc=0; self.probing=0
                self.text=[]
            def reset(self,p): self.lines=p
            def _dim_sizes_set(self,ent,last,first): ent.update(last=last,first=first)
            def var_size(self,ent,t): return 5*(ent['first'] or 1)*ent['last']
            def emit(self,s,*a):self.text.append(s)
            def ld_hl_ind(self,x): self.text.append('ld hl,('+str(x)+')')
        cls=with_literal_redims(Base,real_type=0,runtime_memfill=7)
        x=cls();x.reset([row(10,'\xe9A(5)'),row(20,'\xe9A(2)')])
        x._dim_sizes_set(x.arrays[0],5,0)
        x._dim_sizes_set(x.arrays[0],2,0)
        self.assertEqual(x.arrays[0]['last'],5)
        self.assertEqual(x.var_size(x.arrays[0],0),27)
        self.assertEqual(x.arrays[0]['zxux_slot'],125)
        x._guard_index(125)
        self.assertTrue(any('sbc hl,de' in t for t in x.text))
        self.assertTrue(any('rst 8; defb 3' in t for t in x.text))
        self.assertIn('ld hl,(125)',x.text)


if __name__=='__main__': unittest.main()
