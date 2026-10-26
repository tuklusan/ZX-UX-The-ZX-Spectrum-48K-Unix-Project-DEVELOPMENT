"""Validate precise mnemonic and opcode capture without disassembling code."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_instructions import (UnresolvedInstruction, inspect_sources,
                                   verify_three_sources)


def emit(kind, source, payload, position):
    return SimpleNamespace(kind=kind, source=source, position=position,
                           data=bytes(payload))


def asm(text):
    table = {'ld a,0': b'\x3e\x00', 'jp 0': b'\xc3\x00\x00',
             'ret': b'\xc9', 'nop': b'\x00'}
    return table[text]


class InstructionTests(unittest.TestCase):
    def test_actual_mnemonic_and_word_opcode_before_encoding(self):
        data = b'\x3e\x00\xc3\x11\x22\xc9'
        events = [emit('instruction', 'ld a,0', data[:2], 0),
                  emit('opcode', 'jp nn', data[2:3], 2),
                  emit('instruction', 'ret', data[5:], 5)]
        records = inspect_sources(events, data, asm)
        report = verify_three_sources([records, records, records], (0x8000, 0x7000, 0x6000))
        self.assertEqual(report['typed_source_bytes'], 4)
        self.assertEqual(report['kind_counts'], {'mnemonic': 2, 'word_opcode': 1})
        self.assertFalse(report['fully_symbolic'])

    def test_changed_byte_is_explicit_not_admitted(self):
        row = inspect_sources([emit('instruction', 'ret', b'\xc9', 0)], b'\x76', asm)
        self.assertTrue(row[0].overwritten)

    def test_fake_mnemonic_and_unknown_opcode_fail(self):
        for event in (emit('instruction', 'nop', b'\xc9', 0),
                      emit('opcode', 'ret', b'\xc9', 0),
                      emit('instruction', 'wrong', b'\x00', 0)):
            with self.subTest(event=event.source), self.assertRaises(UnresolvedInstruction):
                inspect_sources([event], bytes(event.data), asm)

    def test_out_of_range_source_location_fails(self):
        with self.assertRaises(UnresolvedInstruction):
            inspect_sources([emit('instruction', 'ret', b'\xc9', 2)], b'\x00', asm)

    def test_source_layout_mismatch_fails_closed(self):
        a = inspect_sources([emit('instruction', 'ret', b'\xc9', 0)], b'\xc9', asm)
        b = inspect_sources([emit('instruction', 'ret', b'\xc9', 1)], b'\x00\xc9', asm)
        with self.assertRaises(UnresolvedInstruction):
            verify_three_sources([a, a, b], (0x8000, 0x7000, 0x6000))


if __name__ == '__main__':
    unittest.main()
