"""Do not allow legacy fragment optimization to masquerade as Gate 8."""
from __future__ import annotations

import types
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from whole_program_codegen import UnresolvedAssemblyBoundary, install


class Mock:
    def __init__(self):
        self.far = bytearray(16)
        self.pc = 0
        self.counting = False
        self.de_flags = 0
        self._zxux_capture = None
        self.reset(None)

    @property
    def storing(self):
        return True

    def reset(self, source):
        self.pc = 0

    def emit_byte(self, value):
        self.far[self.pc] = value
        self.pc += 1

    def emit_word(self, value):
        self.emit_byte(value & 255)
        self.emit_byte(value >> 8)

    def emit_word_reloc(self, value):
        self.emit_word(value)

    def emit_bytes(self, data):
        for b in data:
            self.emit_byte(b)

    def emit(self, text, *args):
        self.emit_byte(0xc9)

    def emit_opcode(self, text):
        self.emit_byte(0xc3)

    def compile_whole(self, program):
        self.emit('ret')
        # A direct memory write is an unresolved producer.
        self.far[self.pc] = 0x76
        self.pc += 1
        return types.SimpleNamespace(ok=True, mode='C', code=bytes(self.far[:self.pc]))


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(types.SimpleNamespace(Compiler=Mock))

    def test_uncaptured_bytes_refused(self):
        candidate = Mock()
        with self.assertRaisesRegex(UnresolvedAssemblyBoundary, '1 uncaptured bytes'):
            candidate.compile_whole(b'')
        self.assertEqual(candidate._zxux_upeep_stats['uncovered_bytes'], 1)

    def test_cannot_install_twice(self):
        install(types.SimpleNamespace(Compiler=Mock))
        candidate = Mock()
        with self.assertRaises(UnresolvedAssemblyBoundary):
            candidate.compile_whole(b'')


if __name__ == '__main__':
    unittest.main()
