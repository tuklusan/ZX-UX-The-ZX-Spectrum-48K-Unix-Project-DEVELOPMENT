"""Only original zero-BSS STKEND end markers may address a boundary."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from stkend_end_pointer import original_stkend_end_marker
from symbolic_capture import Emission
from symbolic_relocations import inspect_relocations, UnresolvedRelocation
from symbolic_source_boundaries import inspect_source_boundaries, SourceBoundaryError


class EndPointer(unittest.TestCase):
    def fixture(self, base=0x8000):
        image = b'\x00\x00\x00\x21' + (base + 9).to_bytes(2, 'little') + b'\x22\x6c\x5c'
        events = [Emission(3, 'opcode', 'ld hl,nn', b'\x21'),
                  Emission(4, 'relocation', '(9,)', image[4:6], 9),
                  Emission(6, 'instruction', 'ld ($5C6C),hl', image[6:9])]
        return image, events

    def test_exact_original_stkend_witness(self):
        image, events = self.fixture()
        self.assertTrue(original_stkend_end_marker(events, image, 0x8000, 0, 4, 9))
        words = inspect_relocations(events, image, 0x8000, 0)
        self.assertEqual(words[0].target_offset, 9)

    def test_no_generic_out_of_range_exemption(self):
        image, events = self.fixture()
        candidates = [
            (events, 1, 4, 9),  # nonzero BSS must obey its ordinary bounds
            (events, 0, 3, 9),
            (events, 0, 4, 10),
            (events[:2], 0, 4, 9),
            (events + [events[2]], 0, 4, 9),
            ([replace(events[2], source='ld ($5C36),hl')]+events[:2], 0, 4, 9),
            ([replace(events[0], source='jp nn')]+events[1:], 0, 4, 9),
            ([replace(events[1], data=b'\x00\x00')]+events[0:1]+events[2:], 0, 4, 9),
        ]
        for variant, bss, site, target in candidates:
            with self.subTest(case=(bss, site, target, variant)):
                self.assertFalse(original_stkend_end_marker(
                    variant, image, 0x8000, bss, site, target))
        with self.assertRaisesRegex(UnresolvedRelocation, 'beyond code and BSS'):
            inspect_relocations([replace(events[1], symbol_offset=10)], image, 0x8000, 0)


if __name__ == '__main__':
    unittest.main()
