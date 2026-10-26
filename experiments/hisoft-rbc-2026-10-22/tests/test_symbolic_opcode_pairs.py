"""Typed source opcode-plus-relocation regression tests."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_opcode_pairs import (UnresolvedOpcode, inspect_opcode_pairs,
                                   verify_three_opcode_passes)


def word(base, offset):
    return ((base + offset) & 65535).to_bytes(2, 'little')


def capture(base, offset=20, overwrite=False, include_word=True):
    op = SimpleNamespace(kind='opcode', position=0,
                         source='jp nn', data=b'\xc3')
    target = SimpleNamespace(kind='relocation', position=1,
                             symbol_offset=offset, data=word(base, offset))
    program = b'\xc3' + word(base, offset)
    if overwrite:
        program = b'\xc3\x0b\x00'
    events = [op, target] if include_word else [op]
    return inspect_opcode_pairs(events, program, base,
                                lambda s: b'\xc3' + int(s.split()[1]).to_bytes(2, 'little'))


class OpcodePairs(unittest.TestCase):
    def test_three_realistic_bases_and_relative_word(self):
        bases = (0xdd71, 0xdbec, 0xdb08)
        report = verify_three_opcode_passes([capture(b) for b in bases], bases)
        self.assertEqual(report['paired_instructions'], 1)
        self.assertEqual(report['paired_instruction_bytes'], 3)
        self.assertTrue(report['fully_symbolic'])

    def test_rewritten_pair_not_claimed_as_symbolic(self):
        bases = (0xdd71, 0xdbec, 0xdb08)
        report = verify_three_opcode_passes([capture(b,overwrite=True) for b in bases], bases)
        self.assertEqual(report['overwritten_pair_count'], 1)
        self.assertFalse(report['fully_symbolic'])

    def test_wrong_target_fails_pass_equivalence(self):
        bases = (0xdd71, 0xdbec, 0xdb08)
        records = [capture(b) for b in bases]
        records[2] = capture(bases[2], offset=19)
        with self.assertRaises(UnresolvedOpcode):
            verify_three_opcode_passes(records, bases)

    def test_missing_operand_is_never_fabricated(self):
        with self.assertRaises(UnresolvedOpcode):
            capture(0x8000, include_word=False)

    def test_unsupported_source_template_is_rejected(self):
        bad = [SimpleNamespace(kind='opcode', position=0,
                               source='ret', data=b'\xc9')]
        with self.assertRaises(UnresolvedOpcode):
            inspect_opcode_pairs(bad, b'\xc9', 0x7000, lambda _: b'\xc9')


if __name__ == '__main__':
    unittest.main()
