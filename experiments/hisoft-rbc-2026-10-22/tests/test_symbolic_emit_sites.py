"""Source-site recording and three-base emission consistency tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))

from symbolic_capture import install
from symbolic_emit_sites import (EmitSiteError, inspect_emit_sites,
                                 verify_three_emit_sites)


class Mini:
    def __init__(self):
        self.far = bytearray(16)
        self.pc = 0
        self.storing = True
        self.reset()

    def reset(self):
        self.pc = 0

    def emit(self, source, *args):
        self.far[self.pc] = 0xc9
        self.pc += 1

    def emit_bytes(self, data):
        self.far[self.pc:self.pc + len(data)] = data
        self.pc += len(data)

    def emit_byte(self, value):
        self.far[self.pc] = value & 255
        self.pc += 1

    def emit_word(self, value):
        self.emit_byte(value)
        self.emit_byte(value >> 8)

    def emit_word_reloc(self, value):
        self.emit_word(value)

    def emit_opcode(self, source):
        self.emit_byte(0xc3)

    def from_original_source(self):
        self.emit('ret')


class Sites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(SimpleNamespace(Compiler=Mini))

    def test_record_original_calling_method_and_line(self):
        obj = Mini()
        obj.from_original_source()
        event = obj._zxux_capture.events[0]
        self.assertRegex(event.source_site, r'^from_original_source:\d+$')
        owned = inspect_emit_sites(obj._zxux_capture.events)
        self.assertEqual(owned[0].site, event.source_site)
        stats = verify_three_emit_sites([owned] * 3, [0x6000, 0x6100, 0x6200])
        self.assertEqual(stats['source_emissions'], 1)
        self.assertFalse(stats['typed_absolute_operands'])

    def test_untyped_runtime_does_not_gain_false_source_site(self):
        event = SimpleNamespace(kind='runtime-opaque', position=0,
                                data=b'\xc9', source_site=None)
        self.assertEqual(inspect_emit_sites([event]), ())

    def test_runtime_source_requires_all_byte_pc_origins(self):
        def e(pcs, site='runtime_pc:0'):
            return SimpleNamespace(kind='instruction', position=0,
                                   data=b'\xc9\x00', source_site=site,
                                   producer_pcs=pcs)
        observed = inspect_emit_sites([e((0, 0x7110))])
        self.assertEqual(observed[0].site, 'runtime_pc:0')
        self.assertEqual(observed[0].producer_pcs, (0, 0x7110))
        for bad in ((), (0,), (0, 65536), (1, 0x7110)):
            with self.subTest(bad=bad), self.assertRaises(EmitSiteError):
                inspect_emit_sites([e(bad)])
        with self.assertRaises(EmitSiteError):
            inspect_emit_sites([e(None)])
        with self.assertRaises(EmitSiteError):
            inspect_emit_sites([e((0, 0x7110), site='runtime_pc:65536')])
        with self.assertRaises(EmitSiteError):
            inspect_emit_sites([e((0, 0x7110), site='emit_const:1')])
        with self.assertRaises(EmitSiteError):
            verify_three_emit_sites([observed, observed,
                inspect_emit_sites([e((0, 0x7111))])], [0x6000, 0x6100, 0x6200])

    def test_missing_site_and_changed_three_pass_source_fail(self):
        def e(site):
            return SimpleNamespace(kind='instruction', position=0,
                                   data=b'\xc9', source_site=site)
        with self.assertRaises(EmitSiteError):
            inspect_emit_sites([e(None)])
        with self.assertRaises(EmitSiteError):
            inspect_emit_sites([e('x:0')])
        original = inspect_emit_sites([e('emit_const:70')])
        different = inspect_emit_sites([e('emit_const:71')])
        with self.assertRaises(EmitSiteError):
            verify_three_emit_sites([original, original, different],
                                    [0x6000, 0x6100, 0x6200])


if __name__ == '__main__':
    unittest.main()
