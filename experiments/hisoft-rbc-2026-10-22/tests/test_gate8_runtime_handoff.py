"""Fail-closed native runtime handoff from three typed source passes."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
from symbolic_capture import Emission
from gate8_runtime_handoff import RuntimeHandoffError, verify_three_runtime_handoffs
from z80asm import asm


class RuntimeHandoffTests(unittest.TestCase):
    BASES = (0x6000, 0x6100, 0x6200)

    def setUp(self):
        self.image = b'\xc9\x00\x01\xff\xff'
        self.events = (
            Emission(0, 'instruction', 'ret', b'\xc9', source_site='emit:1'),
            Emission(1, 'runtime-opaque', 'RT1', b'\x00\x01', source_site='runtime:1'),
            Emission(3, 'word', '(65535,)', b'\xff\xff',
                     source_site='emit_line_table:2455'),
        )
        self.native = {'native_region_verified': True, 'passes': 3,
                       'runtime_start': 1, 'runtime_bytes': 2, 'routines': 1}

    def check(self, events=None, images=None, native=None):
        groups = events if events is not None else [self.events] * 3
        images = images if images is not None else [self.image] * 3
        return verify_three_runtime_handoffs(
            groups, images, self.BASES, [len(self.image)]*3,
            [0]*3, asm, self.native if native is None else native)

    def test_complete_runtime_boundaries_with_source_owned_line_table(self):
        result = self.check()
        self.assertTrue(result['runtime_handoff_verified'])
        self.assertEqual(result['normalized_source_unresolved_bytes'], 2)
        self.assertEqual(result['normalized_source_overlaps'], 0)
        self.assertEqual(result['normalized_source_mismatches'], 0)
        self.assertEqual(result['normalized_source_gaps'], 0)
        self.assertEqual(result['source_line_table']['table_count'], 1)
        self.assertFalse(result['full_program_optimized'])
        self.assertFalse(result['native_behavior_verified'])

    def test_native_runtime_must_be_independently_linked_at_three_bases(self):
        for changed in ({'native_region_verified': False},
                        {'passes': 2}, {'runtime_start': 0},
                        {'runtime_bytes': 1}, {'routines': 2}):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(RuntimeHandoffError, 'native runtime proof'):
                    self.check(native={**self.native, **changed})

    def test_compiler_image_bytes_cannot_be_relabelled(self):
        with self.assertRaises(ValueError):
            self.check(images=[self.image, self.image, b'\xc9\xff\x01\xff\xff'])
        altered = list(self.events)
        altered[1] = replace(altered[1], data=b'\x12\x01')
        with self.assertRaises(ValueError):
            self.check(events=[self.events, tuple(altered), self.events])

    def test_unowned_extra_byte_is_not_accepted(self):
        other = tuple(self.events) + (Emission(1, 'byte', '(0,)', b'\x00'),)
        with self.assertRaises(ValueError):
            self.check(events=[other] * 3)
        with self.assertRaises(ValueError):
            self.check(events=[self.events[:-1]] * 3)

    def test_different_base_or_missing_native_proof_is_rejected(self):
        with self.assertRaisesRegex(RuntimeHandoffError, 'three distinct'):
            verify_three_runtime_handoffs([self.events]*3, [self.image]*3,
                                          [0x6000]*3, [5]*3, [0]*3, asm, self.native)
        with self.assertRaisesRegex(RuntimeHandoffError, 'native runtime proof'):
            self.check(native={})


if __name__ == '__main__':
    unittest.main()
