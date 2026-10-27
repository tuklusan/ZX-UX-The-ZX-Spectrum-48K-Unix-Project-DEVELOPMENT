"""Source-owned literal protection for exact original HiSoft call sites."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from symbolic_capture import Emission
from symbolic_original_literals import (OriginalLiteralError,
    protect_original_literals, protect_three_original_literals)
from symbolic_source_boundaries import inspect_source_boundaries, SourceBoundaryError


def number_events(base=0x6000):
    data = b'\0\0\x05\0\0'
    entries = [Emission(0, 'opcode', 'call nn', b'\xcd', source_site='emit_op_reloc:283'),
               Emission(1, 'relocation', '(8,)', (base+8).to_bytes(2, 'little'), 8,
                        source_site='emit_op_reloc:284')]
    entries.extend(Emission(3+i, 'byte', f'({byte},)', bytes((byte,)),
                            source_site='emit_const:511') for i, byte in enumerate(data))
    return entries, b'\xcd' + (base+8).to_bytes(2, 'little') + data


def string_events():
    data = b'Hi\x00!'
    records = [Emission(0, 'instruction', 'defw 4', b'\x04\0',
                        source_site='emit_string_inline:1203')]
    records.extend(Emission(2+i, 'byte', f'({byte},)', bytes((byte,)),
                            source_site='emit_string_inline:1214')
                   for i, byte in enumerate(data))
    return records, b'\x04\0' + data


class LiteralOwnership(unittest.TestCase):
    def test_original_numeric_source_is_not_z80_instruction(self):
        entries, image = number_events()
        typed, report = protect_original_literals(entries, image)
        self.assertEqual([x.kind for x in typed], ['opcode', 'relocation', 'inline-data'])
        self.assertEqual(typed[-1].data, image[3:])
        self.assertEqual(report['protected_literal_bytes'], 5)
        self.assertEqual(report['numeric_literals'], 1)

    def test_source_derived_string_length_and_control_bytes_preserved(self):
        entries, image = string_events()
        typed, report = protect_original_literals(entries, image)
        self.assertEqual(len(typed), 2)
        self.assertEqual(typed[-1].data, b'Hi\0!')
        self.assertEqual(report['string_literals'], 1)
        self.assertEqual(report['protected_literal_bytes'], 4)

    def test_two_distinct_source_literal_kinds_cannot_be_mixed(self):
        entries, image = string_events()
        changed = list(entries)
        changed[3] = replace(changed[3], source_site='emit_const:511')
        with self.assertRaises(OriginalLiteralError):
            protect_original_literals(changed, image)

    def test_truncated_real_number_refused(self):
        events, image = number_events()
        with self.assertRaisesRegex(OriginalLiteralError, 'five bytes'):
            protect_original_literals(events[:-1], image[:-1])

    def test_numeric_requires_original_stack_call(self):
        events, image = number_events()
        bad = list(events)
        bad[0] = replace(bad[0], source='ld hl,nn')
        with self.assertRaisesRegex(OriginalLiteralError, 'stack-call'):
            protect_original_literals(bad, image)

    def test_string_requires_original_exact_length_header(self):
        events, image = string_events()
        bad = list(events)
        bad[0] = replace(bad[0], source='defw 3')
        with self.assertRaisesRegex(OriginalLiteralError, 'length'):
            protect_original_literals(bad, image)

    def test_byte_source_and_image_must_agree(self):
        events, image = number_events()
        bad = list(events)
        bad[4] = replace(bad[4], source='(44,)')
        with self.assertRaisesRegex(OriginalLiteralError, 'differs'):
            protect_original_literals(bad, image)
        with self.assertRaisesRegex(OriginalLiteralError, 'differs'):
            protect_original_literals(events, image[:-1] + b'\x90')

    def test_three_bases_protect_same_data(self):
        pairs = [number_events(b) for b in (0x6000, 0x6100, 0x6200)]
        groups, images = zip(*pairs)
        typed, report = protect_three_original_literals(groups, images)
        self.assertEqual(report['numeric_literals'], 1)
        self.assertTrue(all(g[-1].data == b'\0\0\x05\0\0' for g in typed))

    def test_three_bases_reject_different_literal(self):
        pairs = [number_events(b) for b in (0x6000, 0x6100, 0x6200)]
        groups, images = [list(p[0]) for p in pairs], [p[1] for p in pairs]
        groups[2][4] = replace(groups[2][4], source='(7,)', data=b'\x07')
        images[2] = images[2][:5] + b'\x07' + images[2][6:]
        with self.assertRaisesRegex(OriginalLiteralError, 'differ across'):
            protect_three_original_literals(groups, images)

    def test_missing_original_site_is_not_promoted(self):
        entries, image = number_events()
        entries[3] = replace(entries[3], source_site='some_other_emitter:511')
        with self.assertRaises(OriginalLiteralError):
            protect_original_literals(entries, image)

    def test_source_boundary_accepts_exact_protected_bytes(self):
        events, image = string_events()
        typed, _ = protect_original_literals(events, image)
        def asm(text):
            if text == 'defw 4':
                return b'\x04\0'
            raise ValueError(text)
        m = inspect_source_boundaries(typed, image, 0x6000, len(image), 0, asm)
        self.assertTrue(m.fully_typed)
        self.assertEqual([(s.kind, s.end-s.start) for s in m.spans],
                         [('inline-data', 2), ('inline-data', 4)])
        with self.assertRaisesRegex(SourceBoundaryError, 'crosses BASIC DATA'):
            inspect_source_boundaries(typed, image, 0x6000, 4, 0, asm)


if __name__ == '__main__':
    unittest.main()
