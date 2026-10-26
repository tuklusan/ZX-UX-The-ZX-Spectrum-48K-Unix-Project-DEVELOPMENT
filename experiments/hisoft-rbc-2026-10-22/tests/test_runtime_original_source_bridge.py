"""Test capture of original HiSoft computed writer roles in the runtime tracer."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_original_runtime_types import HELPER_CODE
from runtime_emitter_trace import RuntimeEmitterTrace, RuntimeTraceError


class SyntheticZ80:
    def __init__(self):
        self.mem = bytearray(65536)
        for address, signature in HELPER_CODE.items():
            self.mem[address:address + len(signature)] = signature
        self.trace = None
        self.sp = 0x5A00
        self.mem[self.sp:self.sp + 2] = b'\x92\x7f'
        self.a = 0xC3
        self.h = self.l = self.d = self.e = 0

    @property
    def hl(self):
        return self.h * 256 + self.l

    @property
    def de(self):
        return self.d * 256 + self.e

    def wb(self, address, value):
        self.mem[address & 65535] = value & 255


class Machine:
    def __init__(self):
        self.p = {'direct': True, 'staging': 0x9000}
        self.cpu = SyntheticZ80()


class RuntimeSourceBridge(unittest.TestCase):
    def test_computed_byte_from_real_helper_is_source_typed(self):
        machine = Machine()
        with RuntimeEmitterTrace(machine, code_base=0x6000) as trace:
            machine.cpu.trace(0x5D16)
            machine.cpu.trace(0x5D25)
            machine.cpu.wb(0x9000, 0xC3)
        result = trace.inspect(0, 1, b'\xc3')
        self.assertTrue(result['source_roles_verified'])
        self.assertEqual(result['typed_calculated_bytes'], 1)
        self.assertEqual(result['untyped_calculated_bytes'], 0)
        self.assertEqual(result['calculated_source_roles'], {'byte': 1})
        self.assertFalse(result['typed_instructions'])

    def test_unknown_computed_writer_rejected(self):
        machine = Machine()
        with self.assertRaisesRegex(RuntimeTraceError, 'untyped'):
            with RuntimeEmitterTrace(machine, code_base=0x6000):
                machine.cpu.trace(0x5D16)
                machine.cpu.trace(0x1234)
                machine.cpu.wb(0x9000, 0xC3)

    def test_original_word_relocation_uses_base_and_source_register(self):
        machine = Machine()
        machine.cpu.h = 0
        machine.cpu.l = 0x35
        with RuntimeEmitterTrace(machine, code_base=0x6000) as trace:
            machine.cpu.trace(0x5D0C)
            machine.cpu.trace(0x5D11)
            machine.cpu.trace(0x5D25)
            machine.cpu.wb(0x9000, 0x35)
            machine.cpu.trace(0x5D25)
            machine.cpu.wb(0x9001, 0x60)
        result = trace.inspect(0, 2, b'5`')
        self.assertEqual(result['calculated_source_roles'],
                         {'reloc-low': 1, 'reloc-high': 1})


if __name__ == '__main__':
    unittest.main()
