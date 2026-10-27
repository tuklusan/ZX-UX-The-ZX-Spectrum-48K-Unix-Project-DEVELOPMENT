"""Live-source instruction and embedded-byte boundary regressions."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_fragments import (FragmentBoundaryError, inspect_fragments, inspect_final_fragments,
                                verify_three_fragment_passes)


def assembler(source):
    return {'rst $28': b'\xef', 'defb $31,$04,$38': b'\x31\x04\x38',
            'inc (hl)': b'\x34', 'ret': b'\xc9', 'nop': b'\x00',
            'jp $6000': b'\xc3\x00\x60', 'jp $6100': b'\xc3\x00\x61',
            'defb $c9': b'\xc9'}[source]


def fragment(source, image, site=0, emitted=None):
    event = SimpleNamespace(kind='instruction', position=site,
                            source=source, data=image[site:] if emitted is None else emitted)
    return inspect_fragments([event], image, len(image), assembler)


class SourceFragments(unittest.TestCase):
    def test_rom_calculator_inline_resource_preserved(self):
        source = 'rst $28; defb $31,$04,$38; inc (hl)'
        records = fragment(source, b'\xef\x31\x04\x38\x34')
        self.assertEqual([(f.kind, f.site, f.end) for f in records],
                         [('instruction', 0, 1), ('inline-data', 1, 4),
                          ('instruction', 4, 5)])
        self.assertEqual(records[1].encoded, b'\x31\x04\x38')

    def test_protected_bytes_may_look_like_code(self):
        records = fragment('rst $28; defb $31,$04,$38', b'\xef\x31\x04\x38')
        self.assertEqual(records[1].kind, 'inline-data')

    def test_final_image_rewrite_is_reported_without_retyping_code(self):
        records = fragment('rst $28; defb $31,$04,$38', b'\xef\x31\x04\x39',
                           emitted=b'\xef\x31\x04\x38')
        self.assertTrue(records[1].overwritten)
        self.assertEqual(records[1].encoded, b'\x31\x04\x38')

    def test_blank_inline_statement_refused(self):
        with self.assertRaises(FragmentBoundaryError):
            fragment('ret;;nop', b'\xc9\x00')

    def test_incomplete_event_refused(self):
        event = SimpleNamespace(kind='instruction', position=0, source='ret',
                                data=b'\xc9\x00')
        with self.assertRaises(FragmentBoundaryError):
            inspect_fragments([event], b'\xc9\x00', 2, assembler)

    def test_source_crossing_data_boundary_refused(self):
        event = SimpleNamespace(kind='instruction', position=0, source='ret',
                                data=b'\xc9')
        with self.assertRaises(FragmentBoundaryError):
            inspect_fragments([event], b'\xc9', 0, assembler)

    def test_runtime_opaque_is_not_source_instruction(self):
        event = SimpleNamespace(kind='runtime-opaque', position=0, source='RT7',
                                data=b'\xc9')
        with self.assertRaises(FragmentBoundaryError):
            inspect_fragments([event], b'\xc9', 1, assembler)

    def test_source_rewrite_cannot_hide_mismatch(self):
        first = SimpleNamespace(kind='instruction', position=0, source='ret',
                                data=b'\xc9')
        second = SimpleNamespace(kind='instruction', position=0, source='nop',
                                 data=b'\x00')
        with self.assertRaises(FragmentBoundaryError):
            inspect_fragments([first, second], b'\x00', 1, assembler)

    def test_final_rewind_requires_fully_replaced_instruction(self):
        first = SimpleNamespace(kind='instruction', position=0,
                                source='ret', data=b'\xc9')
        last = SimpleNamespace(kind='instruction', position=0,
                               source='nop', data=b'\x00')
        live = inspect_final_fragments([first, last], b'\x00', 1, assembler)
        self.assertEqual([(f.source, f.site) for f in live], [('nop', 0)])
        self.assertFalse(live[0].overwritten)

    def test_partial_rewrite_rejected_even_when_byte_matches(self):
        old = SimpleNamespace(kind='instruction', position=0,
                              source='jp $6000', data=b'\xc3\x00\x60')
        new = SimpleNamespace(kind='instruction', position=1,
                              source='nop', data=b'\x00')
        with self.assertRaisesRegex(FragmentBoundaryError, 'partial'):
            inspect_final_fragments([old, new], b'\xc3\x00\x60',
                                    3, assembler)

    def test_historical_opcode_and_word_emissions_do_not_claim_code(self):
        old = SimpleNamespace(kind='instruction', position=0,
                              source='ret', data=b'\xc9')
        opcode = SimpleNamespace(kind='opcode', position=0,
                                 source='call nn', data=b'\xcd')
        live_ret = SimpleNamespace(kind='instruction', position=1,
                                   source='ret', data=b'\xc9')
        fragments = inspect_final_fragments(
            [old, opcode, live_ret], b'\xcd\xc9', 2, assembler)
        self.assertEqual([(f.source, f.site) for f in fragments], [('ret', 1)])

    def test_historical_direct_literal_cannot_be_promoted_to_code(self):
        old = SimpleNamespace(kind='instruction', position=0,
                              source='ret', data=b'\xc9')
        raw = SimpleNamespace(kind='byte', position=0,
                              source='(0,)', data=b'\x00')
        end = SimpleNamespace(kind='instruction', position=1,
                              source='ret', data=b'\xc9')
        fragments = inspect_final_fragments(
            [old, raw, end], b'\x00\xc9', 2, assembler)
        self.assertEqual([(f.source, f.site) for f in fragments], [('ret', 1)])

    def test_original_protected_inline_data_cannot_be_rewritten(self):
        old = SimpleNamespace(kind='instruction', position=0,
                              source='defb $31,$04,$38', data=b'\x31\x04\x38')
        new = SimpleNamespace(kind='instruction', position=0,
                              source='jp $6000', data=b'\xc3\x00\x60')
        with self.assertRaisesRegex(FragmentBoundaryError, 'protected'):
            inspect_final_fragments([old, new], b'\xc3\x00\x60',
                                    3, assembler)

    def test_opaque_replacement_cannot_claim_typed_source(self):
        old = SimpleNamespace(kind='instruction', position=0,
                              source='ret', data=b'\xc9')
        new = SimpleNamespace(kind='runtime-opaque', position=0,
                              source='RT1', data=b'\xc9')
        with self.assertRaisesRegex(FragmentBoundaryError, 'untyped'):
            inspect_final_fragments([old, new], b'\xc9', 1, assembler)

    def test_inline_data_replacement_does_not_count_as_code(self):
        old = SimpleNamespace(kind='instruction', position=0,
                              source='ret', data=b'\xc9')
        later = SimpleNamespace(kind='instruction', position=0,
                                source='defb $c9', data=b'\xc9')
        with self.assertRaisesRegex(FragmentBoundaryError, 'untyped'):
            inspect_final_fragments([old, later], b'\xc9', 1, assembler)

    def test_final_rewrites_agree_at_three_compiler_bases(self):
        originals = []
        for base in (0x6000, 0x6100, 0x6200):
            events = [SimpleNamespace(kind='instruction', position=0,
                                      source='ret', data=b'\xc9'),
                      SimpleNamespace(kind='instruction', position=0,
                                      source='nop', data=b'\x00')]
            originals.append(inspect_final_fragments(events, b'\x00', 1, assembler))
        self.assertEqual(verify_three_fragment_passes(
            originals, (0x6000, 0x6100, 0x6200))['instruction_statements'], 1)

    def test_three_native_bases_preserve_inline_data(self):
        groups = [fragment('rst $28; defb $31,$04,$38', b'\xef\x31\x04\x38')
                  for _ in range(3)]
        report = verify_three_fragment_passes(groups, [0x5b00, 0x5a00, 0x5900])
        self.assertEqual(report['protected_inline_bytes'], 3)
        self.assertEqual(report['instruction_bytes'], 1)
        self.assertFalse(report['complete_program_symbolic'])

    def test_three_bases_detect_changed_patch_status(self):
        stable = fragment('ret', b'\xc9')
        altered = fragment('ret', b'\x00', emitted=b'\xc9')
        with self.assertRaises(FragmentBoundaryError):
            verify_three_fragment_passes([stable, altered, stable],
                                         [0x6000, 0x6100, 0x6200])

    def test_three_bases_detect_changed_immediate(self):
        groups = [fragment('jp $6000', b'\xc3\x00\x60'),
                  fragment('jp $6100', b'\xc3\x00\x61'),
                  fragment('jp $6000', b'\xc3\x00\x60')]
        report = verify_three_fragment_passes(groups, [0x6000, 0x6100, 0x6200])
        self.assertEqual(report['code_statements_varying_across_bases'], 1)

    def test_three_bases_reject_changed_protected_data(self):
        same = fragment('rst $28; defb $31,$04,$38', b'\xef\x31\x04\x38')
        changed = fragment('rst $28; defb $31,$04,$38; inc (hl)', b'\xef\x31\x04\x38\x34')
        with self.assertRaises(FragmentBoundaryError):
            verify_three_fragment_passes([same, changed, same], [0x6000, 0x6100, 0x6200])

    def test_three_bases_must_be_distinct(self):
        run = fragment('ret', b'\xc9')
        with self.assertRaises(FragmentBoundaryError):
            verify_three_fragment_passes([run] * 3, [0x6000] * 3)


if __name__ == '__main__':
    unittest.main()
