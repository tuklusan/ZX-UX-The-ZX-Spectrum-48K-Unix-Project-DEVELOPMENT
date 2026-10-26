"""Test capture of original HiSoft computed writer roles in the runtime tracer."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_original_runtime_types import (HELPER_CODE, OriginalEmitter,
    compiler_image, BASES, N_ROUTINES, TABLE, STAGING)
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


class NativeOriginalRuntimeTrace(unittest.TestCase):
    """Use the real 48K Z80 CPU while the normal compiler tracer is installed."""

    def test_all_original_emitter_producers_reach_live_trace(self):
        tape = Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx')
        if not tape.is_file():
            self.skipTest('operator-supplied compiler tape absent')
        code = compiler_image(tape.read_bytes())
        rom = (Path(__file__).resolve().parents[3] /
               'src/zx-ux-sdk/rom/48.rom').read_bytes()

        class Adapter:
            def __init__(self, machine):
                self.real = machine.cpu
                self.mem = machine.mem
                self.trace = None
                self.original_write = machine._write

            def __getattr__(self, name):
                return getattr(self.real, name)

            @property
            def hl(self):
                return (self.real.h << 8) | self.real.l

            @property
            def de(self):
                return (self.real.d << 8) | self.real.e

            def wb(self, address, value):
                return self.original_write(address, value)

        total_calculated = total_copied = live = 0
        for base in BASES:
            for n in range(1, N_ROUTINES + 1):
                machine = OriginalEmitter(code, rom, base)
                table = TABLE + 2 * (n - 1)
                entry = int.from_bytes(machine.mem[table:table + 2], 'little')
                if not entry:
                    continue
                proxy = Adapter(machine)
                machine.cpu.write_byte = lambda a, v: proxy.wb(a, v)
                wrapper = type('Wrapper', (), {'cpu': proxy,
                    'p': {'direct': True, 'staging': STAGING}})()
                machine.cpu.sp = 0x5a00
                machine.cpu._push_word(0xffff)
                machine.cpu.pc = entry
                with RuntimeEmitterTrace(wrapper, code_base=base) as trace:
                    for _ in range(10000):
                        pc = machine.cpu.pc
                        if pc == 0xffff:
                            break
                        machine.at_pc = pc
                        proxy.trace(pc)
                        machine.type_source.step(machine.cpu, pc)
                        machine.cpu.step()
                    else:
                        self.fail('original HiSoft emitter exceeded step budget')
                end = int.from_bytes(machine.mem[0x44ef:0x44f1], 'little')
                image = bytes(machine.mem[STAGING:STAGING + end])
                report = trace.inspect(0, end, image)
                self.assertTrue(report['fully_observed'], f'RT{n}')
                self.assertTrue(report['source_roles_verified'], f'RT{n}')
                self.assertEqual(report['untyped_calculated_bytes'], 0, f'RT{n}')
                self.assertFalse(report['typed_instructions'])
                self.assertEqual(report['typed_calculated_bytes'],
                                 len(machine.type_source.finish()))
                total_calculated += report['typed_calculated_bytes']
                total_copied += end - report['typed_calculated_bytes']
                live += 1
        self.assertEqual((live, total_calculated, total_copied),
                         (121 * 3, 256 * 3, 1110 * 3))


if __name__ == '__main__':
    unittest.main()
