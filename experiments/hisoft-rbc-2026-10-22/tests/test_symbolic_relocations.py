"""Fail-closed source relocation checks independent of finished SSX code."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_relocations import (UnresolvedRelocation, inspect_relocations,
                                  verify_three_builds)


def make(base, target=18, site=2, image_len=28, overwritten=False):
    image = bytearray(image_len)
    encoded = (base + target) & 65535
    data = encoded.to_bytes(2, 'little')
    image[site:site + 2] = b'\x08\x00' if overwritten else data
    event = SimpleNamespace(kind='relocation', position=site,
                            symbol_offset=target, data=data, source='18')
    return inspect_relocations([event], bytes(image), base, 6)


class Relocations(unittest.TestCase):
    def test_three_distinct_native_bases(self):
        bases = (0xDD71, 0xDBEC, 0xDB08)
        report = verify_three_builds([make(b) for b in bases], bases)
        self.assertEqual(report['verified_encoded_relocation_bytes'], 2)
        self.assertEqual(report['verified_distinct_bases'], 3)
        self.assertTrue(report['fully_symbolic'])

    def test_overwritten_source_operand_is_not_accepted_as_symbolic(self):
        bases = (0xDD71, 0xDBEC, 0xDB08)
        result = verify_three_builds([make(b, overwritten=True) for b in bases], bases)
        self.assertEqual(result['overwritten_relocation_events'], 1)
        self.assertFalse(result['fully_symbolic'])

    def test_source_operand_changes_with_base(self):
        bases = (0xDD71, 0xDBEC, 0xDB08)
        data = [make(b) for b in bases]
        data[2] = make(bases[2], target=17)
        with self.assertRaises(UnresolvedRelocation):
            verify_three_builds(data, bases)

    def test_duplicate_base_is_not_a_relocation_proof(self):
        with self.assertRaises(UnresolvedRelocation):
            verify_three_builds([make(0x8000)] * 3, (0x8000,) * 3)

    def test_out_of_bounds_and_wrong_encoded_bytes(self):
        base = 0x7000
        for target in (-1, 35, 65536):
            event = SimpleNamespace(kind='relocation', position=2,
                                    symbol_offset=target, data=b'\0\0', source='x')
            with self.assertRaises(UnresolvedRelocation):
                inspect_relocations([event], bytes(28), base, 6)
        event = SimpleNamespace(kind='relocation', position=2,
                                symbol_offset=5, data=b'\0\0', source='x')
        with self.assertRaises(UnresolvedRelocation):
            inspect_relocations([event], bytes(28), base, 6)

    def test_non_source_bytes_never_become_relocations(self):
        event = SimpleNamespace(kind='runtime-opaque', position=2,
                                symbol_offset=18, data=b'\x18\x70', source='RT6')
        with self.assertRaises(UnresolvedRelocation):
            inspect_relocations([event], bytes(28), 0x7000, 6)


if __name__ == '__main__':
    unittest.main()
