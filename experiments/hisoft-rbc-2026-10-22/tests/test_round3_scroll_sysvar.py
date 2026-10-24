"""SCR_CT uses a private process byte, not ZX-UX memory at 23692."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from spectrum_sysvars import ProcessSystemVariables, SCR_CT
from native_sysvars_rt import _native_peek, _native_poke
from native_sysvar_policy import allow_private_sysvars
from poke_policy import apply_poke_policy, ProtectedPoke
from z80asm import asm
from z80mini import Z80


class ScrollCounterIsolation(unittest.TestCase):
    def test_process_state_is_byte_exact_and_isolated(self):
        first, second = ProcessSystemVariables(), ProcessSystemVariables()
        first.poke(SCR_CT, 255)
        self.assertEqual(first.peek(SCR_CT),255)
        self.assertNotEqual(second.peek(SCR_CT),255)
        first.poke(SCR_CT, 257)
        self.assertEqual(first.peek(SCR_CT),1)

    def test_compile_time_static_and_dynamic_policy(self):
        finding=SimpleNamespace(line=10,operation='POKE',severity='block',classification='system_or_kernel',expression='23692,255')
        self.assertEqual(allow_private_sysvars([finding]),1)
        self.assertEqual(finding.severity,'info')
        proof={'line':10,'addresses':[{'space':'absolute','offset':23692}]}
        apply_poke_policy([finding],[proof])
        self.assertEqual(finding.classification,'process_sysvar_poke')
        with self.assertRaises(ProtectedPoke):
            apply_poke_policy([SimpleNamespace(line=10,operation='POKE',severity='block',classification='system_or_kernel')],
                              [{'line':10,'addresses':[{'space':'absolute','offset':23693}]}])

    def test_real_native_peek_poke_preserves_kernel_storage(self):
        mem=bytearray(65536)
        mem[SCR_CT]=0xcc
        peek_addr=0x7000
        poke_addr=0x7400
        peek_code=_native_peek(asm,0x1000,peek_addr)
        poke_code=_native_poke(asm,0x1000,peek_addr,entry=poke_addr-peek_addr)
        mem[peek_addr:peek_addr+len(peek_code)]=peek_code
        mem[poke_addr:poke_addr+len(poke_code)]=poke_code
        cpu=Z80(mem);cpu.sp=0x9000
        cpu.hl=SCR_CT;cpu.e=0x55;cpu.call(poke_addr)
        cpu.hl=SCR_CT;cpu.call(peek_addr)
        self.assertEqual(cpu.hl,0x55)
        self.assertEqual(mem[SCR_CT],0xcc)
        self.assertEqual(mem[0x8000+12],0x55)

if __name__=='__main__':unittest.main()