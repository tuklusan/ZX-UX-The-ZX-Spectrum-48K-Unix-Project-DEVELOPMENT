"""Check native keyboard scan is limited to ROM KSTATE reads."""
import sys
import types
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from native_keyread_rt import install

class Base:
    def operand_to_int(self): self.actions.append('operand')
    def emit(self,source): self.actions.append(source)

class NativePeekTests(unittest.TestCase):
    def test_single_install_and_register_preservation(self):
        class HiSoft(Base):
            def __init__(self): self.actions=[]
        mod=types.SimpleNamespace(Compiler=HiSoft)
        install(mod)
        install(mod)
        out=HiSoft()
        out.fn_peek()
        self.assertEqual(len(out.actions),2)
        code=out.actions[1].lower()
        self.assertIn('cp $5c',code)
        self.assertIn('cp $04',code)
        self.assertIn('call $02bf',code)
        self.assertIn('ld l,(hl); ld h,0',code)
        for op in ('push af','pop af','push hl','pop hl',
                   'push bc','pop bc','push de','pop de'):
            self.assertIn(op,code)
        self.assertEqual(code.count('call $02bf'),1)

    def test_branch_targets_skip_only_rom_scan(self):
        class HiSoft(Base):
            def __init__(self): self.actions=[]
        install(types.SimpleNamespace(Compiler=HiSoft))
        m=HiSoft();m.fn_peek()
        instructions=[p.strip() for p in m.actions[1].split(';')]
        self.assertEqual(instructions[3],'jr nz,+14')
        self.assertEqual(instructions[6],'jr nz,+9')
        self.assertEqual(instructions[-2:],['ld l,(hl)','ld h,0'])

if __name__=='__main__':unittest.main()