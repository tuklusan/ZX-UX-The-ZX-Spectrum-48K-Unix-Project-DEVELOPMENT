"""Reproducible source-first disassembly gates for original 48K emitters."""
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from gate8_original_runtime_disassembly import (
    BASES, START, RuntimeDisassemblyError, _decode_all, _flow,
    decode_original_copy_sources, disassemble_original_runtime,
)


class SourceFragments(unittest.TestCase):
    def test_original_copied_instruction_is_fully_decoded(self):
        code = bytes.fromhex('21 01 00 c9')
        copy = [(i, value, START + i) for i, value in enumerate(code)]
        self.assertEqual(decode_original_copy_sources(code, b'', copy), (4, 1))

    def test_partial_copy_of_original_instruction_fails(self):
        code = bytes.fromhex('21 01 00 c9')
        with self.assertRaisesRegex(RuntimeDisassemblyError, 'boundary'):
            decode_original_copy_sources(code, b'', [(0, 0x21, START)])

    def test_modified_source_byte_fails(self):
        code = bytes.fromhex('21 01 00 c9')
        with self.assertRaisesRegex(RuntimeDisassemblyError, 'source no longer matches'):
            decode_original_copy_sources(code, b'', [(0, 0xC3, START)])

    def test_protected_rom_source_is_checked(self):
        rom = bytes.fromhex('a7 ed 52')
        copied = [(i, value, i) for i, value in enumerate(rom)]
        self.assertEqual(decode_original_copy_sources(b'', rom, copied), (3, 1))

    def test_branch_cannot_enter_operand(self):
        operations = _decode_all(b'\x18\xff', 0x6000)
        with self.assertRaisesRegex(RuntimeDisassemblyError, 'overlaps instruction'):
            _flow(operations, 2, 0x6000)

    def test_indirect_jump_never_claimed_resolved(self):
        operations = _decode_all(b'\xe9', 0x6000)
        report = _flow(operations, 1, 0x6000)
        self.assertEqual(report['unresolved_indirect_branch'], 1)
        self.assertEqual(report['reachable_instructions'], 1)

    def test_truncated_instruction_rejected(self):
        with self.assertRaisesRegex(RuntimeDisassemblyError, 'boundary'):
            _decode_all(b'\xcd\x00', 0x6000)

    def test_requires_distinct_valid_native_bases(self):
        with self.assertRaisesRegex(RuntimeDisassemblyError, 'three distinct'):
            disassemble_original_runtime(b'', b'', bases=(0x6000, 0x6000, 0x5e1e))


class NativeOriginal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path('/mnt/data/HiSoft_BASIC_v1.1_48K_compiler_only.tzx')
        cls.tape = path.read_bytes() if path.is_file() else None
        cls.rom = (STAGE.parents[2] / 'src/zx-ux-sdk/rom/48.rom').read_bytes()

    def test_real_original_tape_three_base_disassembly(self):
        if self.tape is None:
            self.skipTest('operator-supplied original HiSoft tape absent')
        report = disassemble_original_runtime(self.tape, self.rom)
        for key, value in {
            'runtime_emitters': 121,
            'unused_emitter_slots': 10,
            'original_copied_bytes': 1110,
            'original_source_fragments': 109,
            'typed_computed_bytes': 256,
            'total_output_bytes': 1366,
            'reachable_instructions': 825,
            'internal_branch': 79,
            'rom_branch': 81,
            'unresolved_external_branch': 3,
            'unresolved_indirect_branch': 3,
            'next_routine_fallthrough': 18,
        }.items():
            self.assertEqual(report[key], value, key)
        self.assertEqual(report['bases'], list(BASES))
        self.assertTrue(report['original_source_bytes_verified'])
        self.assertTrue(report['three_base_instruction_boundaries_verified'])
        self.assertFalse(report['whole_program_cross_routine_cfg_verified'])
        self.assertFalse(report['native_optimizer_equivalence_verified'])
        self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()
