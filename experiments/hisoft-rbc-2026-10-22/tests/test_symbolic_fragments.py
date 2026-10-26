"""Live-source instruction and embedded-byte boundary regressions."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_fragments import (FragmentBoundaryError, inspect_fragments,
                                verify_three_fragment_passes)


def assembler(source):
    return {'rst $28': b'\xef', 'defb $31,$04,$38': b'\x31\x04\x38',
            'inc (hl)': b'\x34', 'ret': b'\xc9', 'nop': b'\x00',
            'jp $6000': b'\xc3\x00\x60', 'jp $6100': b'\xc3\x00\x61'}[source]


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
