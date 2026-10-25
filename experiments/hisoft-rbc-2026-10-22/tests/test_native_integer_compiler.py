"""Compiler reset and typing integration, without dependence on game names."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from native_integer_compiler import with_integral_scalars

class Base:
    def reset(self, program):
        self.program=program
        self.names=[]
        self.n_int=0
        self.n_real=0
        self.name_bytes=0
        self.int_directive=0

class Tests(unittest.TestCase):
    def test_predeclared_scalar_layout(self):
        C=with_integral_scalars(Base,['z','a','a'],1)
        obj=C()
        obj.reset(b'abc')
        self.assertEqual(obj.names,[('a',1),('z',1)])
        self.assertEqual(obj.n_int,2)
        self.assertEqual(obj.name_bytes,4)
        self.assertEqual(obj.n_real,0)
        self.assertEqual(obj.int_directive,255)
        obj.reset(b'def')
        self.assertEqual(obj.names,[('a',1),('z',1)])
    def test_empty_program_preserves_base(self):
        self.assertIs(with_integral_scalars(Base,[],1), Base)
    def test_bad_names_fail_closed(self):
        for names in (['long'],['A'],['x$'],['0']):
            with self.assertRaises(ValueError):
                with_integral_scalars(Base,names,1)
    def test_nonempty_name_table_fails_closed(self):
        class Busy(Base):
            def reset(self,p):
                super().reset(p)
                self.names=[('a',0)]
        with self.assertRaises(ValueError):
            with_integral_scalars(Busy,['a'],1)().reset(b'')

if __name__=='__main__':
    unittest.main()
