"""Check 48K ROM entry and compiler dispatch for dynamic VAL."""
import sys
import types
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from native_val_rt import install, _guard_code

class RTModule:
    class Machine:
        def __init__(self):
            self.far = bytearray(1024)
            self.de_flags = 0
            self.calls = []
        def run_emitter(self, n, pc, counting, code_base):
            self.calls.append(n)
            return pc + 2

class CompilerClass:
    def __init__(self, ch=ord('x'), directive=0, typ=128):
        self.char = ch
        self.val_directive = directive
        self.t = typ
        self.calls = []
    def get_char(self): return self.char
    def operand(self): self.calls.append('operand')
    def call_rt(self, n): self.calls.append(('rt',n))
    def fn_val(self): self.calls.append('upstream')
    def not_supported(self, message): raise ValueError(message)

class Module:
    rtlib = RTModule
    STRING = 128
    REAL = 0
    Compiler = CompilerClass

class NativeVal(unittest.TestCase):
    def setUp(self):
        self.module = type('Module',(object,),{'rtlib': type('Runtime',(object,),{'Machine':RTModule.Machine}),
            'STRING':128, 'REAL':0, 'Compiler':type('Compiler',(CompilerClass,),{})})
        from z80asm import asm
        self.guard = _guard_code(asm)
        with patch.dict(sys.modules, {'rtnames':types.SimpleNamespace(RT=types.SimpleNamespace(VAL=109)),
                                      'z80asm':types.SimpleNamespace(asm=asm)}):
            install(self.module)
            install(self.module)
    def test_emit_actual_rom_val(self):
        machine=self.module.rtlib.Machine()
        self.assertEqual(machine.run_emitter(109,10,False,0),10+len(self.guard))
        self.assertEqual(machine.far[10:10+len(self.guard)],self.guard)
        self.assertEqual(machine.run_emitter(109,256,True,0),256+len(self.guard))
        self.assertEqual(machine.far[256:256+len(self.guard)],bytes(len(self.guard)))
        self.assertEqual(machine.run_emitter(108,600,False,0),602)
        self.assertEqual(machine.calls,[108])
    def test_compile_string_expression(self):
        c=self.module.Compiler()
        c.fn_val()
        self.assertEqual(c.calls,['operand',('rt',109)])
        self.assertEqual(c.t,0)
    def test_literal_and_original_directive_unchanged(self):
        for c in [self.module.Compiler(ch=ord('"')),self.module.Compiler(directive=1)]:
            c.fn_val()
            self.assertEqual(c.calls,['upstream'])
    def test_non_string_rejected(self):
        c=self.module.Compiler(typ=2)
        with self.assertRaises(ValueError): c.fn_val()
        self.assertNotIn(('rt',109),c.calls)

if __name__=='__main__':unittest.main()