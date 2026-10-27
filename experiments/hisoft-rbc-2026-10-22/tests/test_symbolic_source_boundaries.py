"""Source-only code and protected DATA ownership regression tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_source_boundaries import (SourceBoundaryError,
    inspect_source_boundaries, verify_three_source_maps)


def e(kind, position, data, source='source', symbol_offset=None):
    return SimpleNamespace(kind=kind, position=position, data=data,
                           source=source, symbol_offset=symbol_offset)


def asm(source):
    return {'nop': b'\x00', 'ret': b'\xc9', 'rst $28': b'\xef',
            'defb $31,$04,$38': b'\x31\x04\x38',
            'inc (hl)': b'\x34',
            'rst $28; defb $31,$04,$38; inc (hl)': b'\xef\x31\x04\x38\x34',
            'jp 24600': b'\xc3\x18\x60',
            'jp 24118': b'\xc3\x36\x5e', 'jp 23890': b'\xc3\x52\x5d'}[source]


def probe(base, target=24):
    program = b'\x00\xc3' + ((base + target) & 65535).to_bytes(2, 'little') + b'\xc3\x00\x76'
    events = [e('instruction', 0, b'\x00', 'nop'),
              e('opcode', 1, b'\xc3', 'jp nn'),
              e('relocation', 2, program[2:4], '24', target),
              e('data-source', 4, b'\xc3\x00\x76', 'BASIC DATA')]
    return inspect_source_boundaries(events, program, base, 4, 30, asm)


class SourceOwnership(unittest.TestCase):
    def test_source_opcode_and_relocation_are_one_instruction(self):
        result = probe(0x6000)
        self.assertEqual(result.instruction_bytes, 4)
        self.assertEqual(result.executable_instruction_count, 2)
        self.assertEqual(result.unresolved_bytes, 0)
        self.assertEqual([x.kind for x in result.spans],
                         ['instruction', 'instruction-relocated', 'data-source'])
        self.assertTrue(result.fully_typed)

    def test_three_bases_track_the_same_source_sites(self):
        bases = [0x6000, 0x5e1e, 0x5d3a]
        result = verify_three_source_maps([probe(b) for b in bases], bases)
        self.assertEqual(result['source_instruction_bytes'], 4)
        self.assertEqual(result['source_byte_kinds']['data-source'], 3)
        self.assertFalse(result['complete_program_symbolic'])

    def test_overwritten_history_may_match_by_coincidence_at_one_base(self):
        # Both sources overlap the same byte in all native passes. A historical
        # value matching the final byte cannot make that byte source-owned.
        def historical(earlier, final):
            return inspect_source_boundaries([
                e('byte', 0, bytes((earlier,)), 'prior'),
                e('direct-write', 0, bytes((final,)), 'last')],
                bytes((final,)), 0x6000, 1, 0, asm)
        bases = [0x6000, 0x5e1e, 0x5d3a]
        passes = [historical(42, 42), historical(17, 42), historical(11, 42)]
        report = verify_three_source_maps(passes, bases)
        self.assertEqual(report['source_history_mismatch_variation_bytes'], 1)
        self.assertEqual(report['source_unresolved_bytes'], 1)
        self.assertTrue(all(q.overlaps == (0,) and not q.fully_typed
                            for q in passes))

    def test_unique_source_mismatch_still_fails_across_bases(self):
        bases = [0x6000, 0x5e1e, 0x5d3a]
        passes = [inspect_source_boundaries(
            [e('byte', 0, b'\x11', 'prior')], final,
            base, 1, 0, asm) for base, final in
            zip(bases, (b'\x11', b'\x22', b'\x11'))]
        self.assertTrue(all(q.unresolved_bytes == 1 for q in passes))
        with self.assertRaisesRegex(SourceBoundaryError, 'changed across'):
            verify_three_source_maps(passes, bases)

    def test_unpaired_opcode_not_promoted_by_matching_machine_bytes(self):
        result = inspect_source_boundaries([e('opcode', 0, b'\xc3', 'jp nn'),
            e('binary', 1, b'\x18\x60')], b'\xc3\x18\x60', 0x6000, 3, 0, asm)
        self.assertEqual(result.instruction_bytes, 0)
        self.assertEqual(result.unresolved_bytes, 3)
        self.assertFalse(result.fully_typed)

    def test_opaque_runtime_is_never_disassembled(self):
        result = inspect_source_boundaries([e('runtime-opaque', 0, b'\xc9')],
                                          b'\xc9', 0x6000, 1, 0, asm)
        self.assertEqual(result.instruction_bytes, 0)
        self.assertEqual(result.unresolved_bytes, 1)

    def test_inline_calculator_bytes_are_protected_not_executable(self):
        image = b'\xef\x31\x04\x38\x34'
        event = e('instruction', 0, image,
                  'rst $28; defb $31,$04,$38; inc (hl)')
        result = inspect_source_boundaries([event], image, 0x6000, 5, 0, asm)
        self.assertEqual([span.kind for span in result.spans],
                         ['instruction', 'inline-data', 'instruction'])
        self.assertEqual(result.instruction_bytes, 2)
        self.assertEqual(result.executable_instruction_count, 2)
        self.assertTrue(result.fully_typed)

    def test_inline_rewrite_remains_visible_as_mismatch(self):
        orig = b'\xef\x31\x04\x38\x34'
        final = b'\xef\x31\x04\x39\x34'
        event = e('instruction', 0, orig,
                  'rst $28; defb $31,$04,$38; inc (hl)')
        result = inspect_source_boundaries([event], final, 0x6000, 5, 0, asm)
        self.assertEqual(result.mismatches, (3,))
        self.assertFalse(result.fully_typed)

    def test_data_that_looks_like_jump_remains_data(self):
        result = inspect_source_boundaries([e('data-source', 0, b'\xc3\x00\x76')],
                                          b'\xc3\x00\x76', 0, 0, 0, asm)
        self.assertEqual(result.instruction_bytes, 0)
        self.assertTrue(result.fully_typed)

    def test_untyped_direct_rewrite_is_detected(self):
        result = inspect_source_boundaries([e('byte', 0, b'\x00'),
             e('direct-write', 0, b'\xc9')], b'\xc9', 0, 1, 0, asm)
        self.assertEqual(result.overlaps, (0,))
        self.assertEqual(result.mismatches, (0,))
        self.assertFalse(result.fully_typed)

    def test_paired_instruction_rewrite_is_not_hidden(self):
        program = b'\xc3\x19\x60'
        result = inspect_source_boundaries([
            e('opcode', 0, b'\xc3', 'jp nn'),
            e('relocation', 1, b'\x18\x60', '24', 24)],
            program, 0x6000, 3, 30, asm)
        self.assertEqual(result.mismatches, (1,))
        self.assertFalse(result.fully_typed)

    def test_missing_bytes_stay_missing(self):
        result = inspect_source_boundaries([e('instruction', 0, b'\xc9', 'ret')],
                                          b'\xc9\x00', 0, 2, 0, asm)
        self.assertEqual(result.gaps, (1,))
        self.assertEqual(result.unresolved_bytes, 1)

    def test_relocation_target_and_encoded_operand_must_agree(self):
        bad = [e('opcode', 0, b'\xc3', 'jp nn'),
               e('relocation', 1, b'\x08\x60', '24', 24)]
        with self.assertRaises(SourceBoundaryError):
            inspect_source_boundaries(bad, b'\xc3\x08\x60', 0x6000, 3, 0, asm)

    def test_instruction_cannot_cross_data_boundary(self):
        with self.assertRaises(SourceBoundaryError):
            inspect_source_boundaries([e('instruction', 0, b'\xc9', 'ret')],
                                      b'\xc9', 0, 0, 0, asm)

    def test_emission_outside_final_image_rejected(self):
        with self.assertRaises(SourceBoundaryError):
            inspect_source_boundaries([e('byte', -1, b'\xc9')],
                                      b'\xc9', 0, 1, 0, asm)

    def test_different_source_sites_across_passes_fail(self):
        bases = [0x6000, 0x5e1e, 0x5d3a]
        records = [probe(b) for b in bases]
        records[-1] = inspect_source_boundaries(
            [e('binary', 0, b'\x00\xc3\x52\x5d\xc3\x00\x76')],
            b'\x00\xc3\x52\x5d\xc3\x00\x76', bases[-1], 7, 10, asm)
        with self.assertRaises(SourceBoundaryError):
            verify_three_source_maps(records, bases)

if __name__ == '__main__':
    unittest.main()
