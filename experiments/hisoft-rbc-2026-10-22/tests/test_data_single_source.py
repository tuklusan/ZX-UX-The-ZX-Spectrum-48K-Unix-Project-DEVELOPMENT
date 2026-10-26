"""BASIC DATA writes have one typed source owner, never duplicate patches."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))

from symbolic_capture import install, TracedRAM


class Compiler:
    def __init__(self):
        self.pc = 0
        self.data_start = 2
        self.data_size = 0
        self.line_no = 10
        self.storing = True
        self.storing_data = True
        self.counting = False
        self.de_flags = 0
        self.vars_start = 5
        self.far = TracedRAM(bytearray(64), self)
        self.reset()

    def reset(self):
        self.pc = 0

    def st_data(self, fail=False):
        where = self.data_start + self.data_size
        self.far[where:where + 3] = b'ABC'
        self.data_size += 3
        if fail:
            raise ValueError('invalid DATA value')

    def emit(self, *args):
        return None

    def emit_bytes(self, *args):
        return None

    def emit_byte(self, *args):
        return None

    def emit_word(self, *args):
        return None

    def emit_word_reloc(self, *args):
        return None

    def emit_opcode(self, *args):
        return None


class DataSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(SimpleNamespace(Compiler=Compiler))

    def test_data_source_has_no_duplicate_direct_byte_events(self):
        c = Compiler()
        c.st_data()
        self.assertEqual([e.kind for e in c._zxux_capture.events],
                         ['data-source'])
        self.assertEqual(c._zxux_capture.events[0].data, b'ABC')
        self.assertEqual(c._zxux_capture.events[0].position, 2)
        self.assertFalse(c._zxux_in_data)

    def test_exception_restores_direct_write_capture(self):
        c = Compiler()
        with self.assertRaisesRegex(ValueError, 'invalid DATA'):
            c.st_data(fail=True)
        self.assertFalse(c._zxux_in_data)
        c.far[0] = 0xc9
        self.assertEqual([e.kind for e in c._zxux_capture.events],
                         ['direct-write'])

    def test_text_patch_during_data_is_never_hidden(self):
        c = Compiler()
        c._zxux_in_data = True
        c.far[0] = 0xc3
        c.far[2:5] = b'ABC'
        self.assertEqual([e.kind for e in c._zxux_capture.events],
                         ['direct-write'])
        self.assertEqual(c._zxux_capture.events[0].position, 0)

    def test_preexisting_data_mode_is_restored(self):
        c = Compiler()
        c._zxux_in_data = True
        c.st_data()
        self.assertTrue(c._zxux_in_data)
        self.assertEqual(len(c._zxux_capture.events), 1)


if __name__ == '__main__':
    unittest.main()
