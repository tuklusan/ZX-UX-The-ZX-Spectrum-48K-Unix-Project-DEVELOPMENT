"""Original-token recognition and generic multidimensional string lowering."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_multidim_strings import _dimensions, with_multidim_strings


def row(n, value):
    return n, value.encode('latin1') + b'\r'


class Shapes(unittest.TestCase):
    def test_arbitrary_names_and_three_four_axes(self):
        rows = [row(10, '\xe9B$(4\x0e\0\0\x04\0\0,3\x0e\0\0\x03\0\0,4\x0e\0\0\x04\0\0)'),
                row(20, '\xe9Q$(9,4,3,5)')]
        self.assertEqual(_dimensions(rows), {1: (4,3,4),16:(9,4,3,5)})

    def test_strings_data_comments_are_never_declarations(self):
        self.assertEqual(_dimensions([
            row(10, '\xf5"\xe9A$(5,4,2)":\xea\xe9B$(2,3,4)'),
            row(20, '\xe4\xe9C$(3,2,3)')]), {})

    def test_dynamic_or_inconsistent_shapes_are_not_guessed(self):
        self.assertEqual(_dimensions([row(10,'\xe9B$(X,3,4)')]), {})
        self.assertEqual(_dimensions([row(10,'\xe9B$(4,3,4)'),row(20,'\xe9B$(4,4,4)')]), {})
        self.assertEqual(_dimensions([row(10,'\xe9B$(0,3,4)')]), {})
        self.assertEqual(_dimensions([row(10,'\xe9B$(256,256,2)')]), {})

    def test_compiler_declaration_uses_full_size_and_restores_tail(self):
        class Base:
            def __init__(self):
                self.strvars = [dict(last=0,first=0,flags=0,addr=500) for _ in range(26)]
                self.out=[];self.ch=0;self.input=[3,4,5]
            def reset(self,p):self.lines=p
            def _dim_sizes_set(self, ent, last, first):ent.update(last=last,first=first)
            def emit(self,fmt,*args): self.out.append(fmt.format(*args))
        cls=with_multidim_strings(Base,string_type=0x80,multiply_rt=5,element_rt=10)
        c=cls();c.reset([row(10,'\xe9M$(3,4,5)')])
        self.assertEqual(c.strvars[12]['zxux_dims'],(3,4,5))


if __name__ == '__main__': unittest.main()
