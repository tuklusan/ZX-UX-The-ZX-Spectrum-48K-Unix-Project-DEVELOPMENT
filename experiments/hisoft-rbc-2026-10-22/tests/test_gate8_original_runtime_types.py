"""Typed Z80 producer-role tests use original compiler helpers, not output decode."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_original_runtime_types import (BASES, START, EmitterTypeError, HELPER_CODE,
    SourceTransactions, OriginalEmitter, audit, compiler_image)


class HelperRoles(unittest.TestCase):
    def setUp(self):
        self.mem = bytearray(65536)
        for at, raw in HELPER_CODE.items():
            self.mem[at:at + len(raw)] = raw
        self.cpu = SimpleNamespace(a=0xC3, b=0, c=0, d=0, e=0, h=0,
                                   l=0, sp=0x5000)
        self.mem[0x5000:0x5002] = b'\x92\x7F'
        self.tracker = SourceTransactions(self.mem, 0x6000)

    def test_one_byte_source_tracks_z80_register_and_caller(self):
        self.tracker.step(self.cpu, 0x5D16)
        self.tracker.write(self.cpu, 0x5D25, 0, 0xC3)
        event, = self.tracker.finish()
        self.assertEqual((event.kind, event.position, event.value,
                          event.source_site, event.target_offset),
                         ('byte', 0, 0xC3, 0x7F92, None))

    def test_one_word_source_tracks_original_z80_registers(self):
        self.cpu.h, self.cpu.l = 0x7C, 0xCB
        self.tracker.step(self.cpu, 0x5D11)
        self.tracker.step(self.cpu, 0x5D16)
        self.tracker.write(self.cpu, 0x5D25, 0, 0xCB)
        self.tracker.step(self.cpu, 0x5D16)
        self.tracker.write(self.cpu, 0x5D25, 1, 0x7C)
        self.assertEqual([e.kind for e in self.tracker.finish()],
                         ['word-low', 'word-high'])

    def test_real_relocation_helper_marks_target_before_bytes(self):
        self.cpu.h, self.cpu.l = 0, 0x21
        self.tracker.step(self.cpu, 0x5D0C)
        self.tracker.step(self.cpu, 0x5D11)
        self.tracker.write(self.cpu, 0x5D25, 0, 0x21)
        self.tracker.write(self.cpu, 0x5D25, 1, 0x60)
        lo, hi = self.tracker.finish()
        self.assertEqual((lo.kind, hi.kind, lo.target_offset, hi.target_offset),
                         ('reloc-low', 'reloc-high', 0x21, 0x21))

    def test_wrong_register_byte_fails(self):
        self.tracker.step(self.cpu, 0x5D16)
        with self.assertRaisesRegex(EmitterTypeError, 'register disagrees'):
            self.tracker.write(self.cpu, 0x5D25, 0, 0xCD)

    def test_unobserved_second_byte_fails(self):
        self.tracker.step(self.cpu, 0x5D11)
        self.tracker.write(self.cpu, 0x5D25, 0, 0)
        with self.assertRaisesRegex(EmitterTypeError, 'did not finish'):
            self.tracker.finish()

    def test_calculated_output_without_helper_refused(self):
        with self.assertRaisesRegex(EmitterTypeError, 'no typed Z80 producer'):
            self.tracker.write(self.cpu, 0x5D25, 0, 0xC3)

    def test_helper_must_be_original_unmodified_machine_code(self):
        self.mem[0x5D11] ^= 1
        with self.assertRaisesRegex(EmitterTypeError, 'differs'):
            SourceTransactions(self.mem, 0x6000)

    def test_bad_source_context_rejected(self):
        self.tracker.step(self.cpu, 0x5D16)
        with self.assertRaisesRegex(EmitterTypeError, 'no typed Z80 producer'):
            self.tracker.write(self.cpu, 0x5D22, 0, 0xC3)


class RealOriginalCompiler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = [Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx')]
        cls.tape = next((p for p in candidates if p.is_file()), None)
        cls.rom = Path(__file__).resolve().parents[3] / 'src/zx-ux-sdk/rom/48.rom'

    def test_rom_copy_cannot_be_relabelled_from_modified_memory(self):
        if self.tape is None:
            self.skipTest('operator-supplied original 48K HiSoft tape absent')
        machine = OriginalEmitter(compiler_image(self.tape.read_bytes()),
                                  self.rom.read_bytes(), BASES[0])
        machine.at_pc = 0x5D55
        machine.mem[0x5D55:0x5D57] = b'\xed\xb0'
        machine.mem[START] ^= 0xFF
        machine.cpu.h, machine.cpu.l = START >> 8, START & 255
        machine.cpu.d, machine.cpu.e = 0x90, 0
        with self.assertRaisesRegex(EmitterTypeError, 'original source region changed'):
            machine._write(0x9000, machine.mem[START])

    def test_real_compiler_three_base_exact_accounting(self):
        if self.tape is None:
            self.skipTest('operator-supplied original 48K HiSoft tape absent')
        result = audit(self.tape.read_bytes(), self.rom.read_bytes())
        self.assertEqual(result['native_bases'], list(BASES))
        self.assertEqual(result['runtime_emitters'], 121)
        self.assertEqual(result['empty_slots'], 10)
        self.assertEqual(result['copied_source_bytes'], 1110)
        self.assertEqual(result['computed_source_bytes'], 256)
        self.assertEqual(result['typed_computed_source_bytes'], 256)
        self.assertEqual(result['untyped_computed_source_bytes'], 0)
        self.assertEqual(result['literal_byte_bytes'], 84)
        self.assertEqual(result['literal_word_bytes'], 72)
        self.assertEqual(result['relocated_word_bytes'], 100)
        self.assertEqual(result['total_output_bytes'], 1366)
        self.assertFalse(result['instruction_boundaries_typed'])
        self.assertFalse(result['full_program_symbolic'])
        self.assertFalse(result['gate8_complete'])

    def test_tape_bytes_must_be_original(self):
        if self.tape is None:
            self.skipTest('operator-supplied original 48K HiSoft tape absent')
        data = bytearray(self.tape.read_bytes())
        data[-2] ^= 1
        with self.assertRaises(ValueError):
            compiler_image(bytes(data))


if __name__ == '__main__':
    unittest.main()
