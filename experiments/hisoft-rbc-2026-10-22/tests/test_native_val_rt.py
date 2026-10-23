"""Inspect VAL dispatch; literal expressions keep original compiler behavior."""
import sys
import types
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from native_val_rt import install


class FakeCompilerModule:
    STRING = 128
    REAL = 0
    class Compiler:
        def __init__(self, char=ord('x'), directive=0, typ=128):
            self.char=char
            self.val_directive=directive
            self.t=typ
            self.events=[]
        def get_char(self): return self.char
        def fn_val(self): self.events.append('upstream')
        def operand(self): self.events.append('operand')
        def call_rt(self,n): self.events.append(('runtime',n))
        def not_supported(self,detail): raise ValueError(detail)


class VALTests(unittest.TestCase):
    def setUp(self):
        self.rt = types.SimpleNamespace(RT=types.SimpleNamespace(VAL=109))
        self.module=type('Module', (), {
            'STRING': 128, 'REAL': 0,
            'Compiler': type('Compiler', (FakeCompilerModule.Compiler,), {})
        })
        with patch.dict(sys.modules, {'rtnames': self.rt}):
            install(self.module)
            install(self.module)

    def test_string_variable_uses_input_val_runtime(self):
        c=self.module.Compiler()
        c.fn_val()
        self.assertEqual(c.events,['operand',('runtime',109)])
        self.assertEqual(c.t,0)

    def test_quoted_literal_is_unchanged(self):
        c=self.module.Compiler(ord('"'))
        c.fn_val()
        self.assertEqual(c.events,['upstream'])

    def test_existing_val_directive_is_unchanged(self):
        c=self.module.Compiler(directive=1)
        c.fn_val()
        self.assertEqual(c.events,['upstream'])

    def test_non_string_rejected(self):
        c=self.module.Compiler(typ=2)
        with self.assertRaises(ValueError):
            c.fn_val()
        self.assertNotIn(('runtime',109),c.events)


if __name__=='__main__':
    unittest.main()
