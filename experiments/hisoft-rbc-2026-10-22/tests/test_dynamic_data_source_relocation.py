"""Only a genuine dynamic DATA parser symbol may become native dw source."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))

from symbolic_capture import Capture, install
from symbolic_source_boundaries import inspect_source_boundaries
from native_data_expressions import _extended_read_body, _extended_read_source
from z80asm import asm


class OriginalDataWriter:
    def __init__(self, base=0x6000, target=9, invalid=False):
        self.pc = 0
        self.data_start = 2
        self.data_size = 0
        self.line_no = 100
        self.storing = True
        self.counting = False
        self.de_flags = 0
        self.code_base = base
        self.vars_start = 7
        self.far = bytearray(40)
        self.symbol = target
        self.invalid = invalid
        self._zxux_data_scalar_targets = []
        self.reset()

    def reset(self):
        self.pc = 0
        self._zxux_capture = Capture()

    @property
    def storing_data(self):
        return True

    def st_data(self):
        where = self.data_start + self.data_size
        target = self.symbol
        descriptor = bytes((0, 0x7E, (self.code_base+target)&255,
                            (self.code_base+target)>>8, 0))
        if self.invalid:
            descriptor = bytes((0, 0x7E, 1, 2, 0))
        self.far[where:where+5] = descriptor
        self._zxux_data_scalar_targets.append((where+2, target))
        self.data_size += 5

    def emit(self, *args): pass
    def emit_opcode(self, *args): pass
    def emit_word_reloc(self, *args): pass
    def emit_word(self, *args): pass
    def emit_byte(self, *args): pass
    def emit_bytes(self, *args): pass


class DynamicDataSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(SimpleNamespace(Compiler=OriginalDataWriter))

    def test_three_bases_have_same_typed_scalar_word_and_exact_original_bytes(self):
        groups = []
        for base in (0x5100, 0x5900, 0x6100):
            writer = OriginalDataWriter(base)
            writer.st_data()
            events = writer._zxux_capture.events
            self.assertEqual([(e.position, e.kind) for e in events],
                             [(2, 'data-source'), (4, 'table-relocated'),
                              (6, 'data-source')])
            ref = events[1]
            self.assertEqual(ref.symbol_offset, 9)
            self.assertEqual(ref.source, 'dw nn')
            self.assertEqual(ref.data, (base + 9).to_bytes(2, 'little'))
            # The synthetic two-byte code prefix is deliberately not claimed
            # as a source instruction; this tests DATA ownership alone.
            image = bytes(writer.far[:writer.vars_start])
            record = inspect_source_boundaries(events, image, base, 2, 16, asm)
            self.assertEqual(record.gaps, (0, 1))
            self.assertEqual(record.overlaps, (0, 1))  # gaps also lack unique owners
            self.assertEqual(record.mismatches, ())
            self.assertEqual(record.spans[1].target, 9)
            groups.append([(e.position, e.kind, e.symbol_offset,
                            None if e.kind == 'table-relocated' else e.data)
                           for e in events])
        self.assertEqual(groups[0], groups[1])
        self.assertEqual(groups[1], groups[2])

    def test_forged_source_address_is_rejected(self):
        writer = OriginalDataWriter(invalid=True)
        with self.assertRaisesRegex(ValueError, 'lacks exact parser witness'):
            writer.st_data()

    def test_extended_read_source_is_bit_identical_to_original_emitter(self):
        for stack_num in (0x33b4, 0x02a0):
            self.assertEqual(bytes(asm(_extended_read_source(stack_num))),
                             _extended_read_body(stack_num))


if __name__ == '__main__':
    unittest.main()
