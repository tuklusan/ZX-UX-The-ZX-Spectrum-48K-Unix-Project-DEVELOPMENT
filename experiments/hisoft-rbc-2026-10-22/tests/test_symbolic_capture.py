"""Ensure the diagnostic capture does not change byte output."""
from pathlib import Path
import sys
import types
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_capture import Capture, Emission, install


class Mock:
    def __init__(self):
        self.far = bytearray(128)
        self.pc = 0
        self.storing = True
        self.reset(None)

    def reset(self, source):
        self.pc = 0

    def emit_byte(self, value):
        self.far[self.pc] = value & 255
        self.pc += 1

    def emit_word(self, value):
        self.emit_byte(value & 255)
        self.emit_byte(value >> 8)

    def emit_word_reloc(self, value):
        self.emit_word(value + 10)

    def emit_bytes(self, content):
        self.far[self.pc:self.pc+len(content)] = content
        self.pc += len(content)

    def emit(self, op, *args):
        text = op.format(*args)
        self.emit_bytes({'nop': b'\0', 'ret': b'\xc9'}[text])

    def emit_opcode(self, text):
        self.emit_bytes({'jp nn': b'\xc3'}[text])


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(types.SimpleNamespace(Compiler=Mock))

    def test_emissions_are_recorded_once(self):
        c = Mock()
        c.emit('nop')
        c.emit_opcode('jp nn')
        c.emit_word_reloc(0x1234)
        c.emit_word(4)
        c.emit_byte(1)
        c.emit_bytes(b'END')
        events = c._zxux_capture.events
        self.assertEqual([x.kind for x in events],
                         ['instruction', 'opcode', 'relocation', 'word', 'byte', 'binary'])
        self.assertEqual(c.far[:c.pc], b'\0\xc3>\x12\x04\0\x01END')
        self.assertEqual(events[2].symbol_offset, 0x1234)

    def test_uncovered_runtime_bytes_reported(self):
        c = Mock()
        c.emit('ret')
        c.far[c.pc] = 0x76
        c.pc += 1
        a = c._zxux_capture.audit(bytes(c.far[:c.pc]))
        self.assertEqual(a['uncovered_first'], [1])
        self.assertFalse(a['safe_to_optimize'])

    def test_direct_ram_patch_is_visible(self):
        c = Mock()
        c.emit_opcode('jp nn')
        c.emit_word_reloc(5)
        c.far[1] = 99
        a = c._zxux_capture.audit(bytes(c.far[:c.pc]))
        self.assertEqual(a['patch_first'], [1])
        self.assertFalse(a['safe_to_optimize'])

    def test_rewind_and_overwrite_not_hidden(self):
        c = Mock()
        c.emit('nop')
        c.pc = 0
        c.emit('ret')
        a = c._zxux_capture.audit(bytes(c.far[:c.pc]))
        self.assertEqual(a['rewritten_bytes'], 1)

    def test_counting_pass_not_recorded(self):
        c = Mock()
        c.storing = False
        c.emit('ret')
        self.assertEqual(c._zxux_capture.events, [])

    def test_reset_clears_old_events(self):
        c = Mock()
        c.emit('ret')
        c.reset(None)
        self.assertEqual(c._zxux_capture.events, [])

    def test_runtime_emitter_is_counted_but_not_optimized(self):
        class Machine:
            def __init__(self):
                self.de_flags = 0
                self.far = bytearray(16)
            def run_emitter(self, n, pc, counting, code_base):
                self.far[pc:pc + 2] = b'\xc9\x00'
                return pc + 2
        class Comp(Mock):
            _zxux_symbolic_capture_installed = False
            def __init__(self):
                self.m = Machine()
                super().__init__()
        install(types.SimpleNamespace(Compiler=Comp, rtlib=types.SimpleNamespace(Machine=Machine)))
        c = Comp()
        end = c.m.run_emitter(7, 0, 0, 0)
        self.assertEqual(end, 2)
        self.assertEqual(c._zxux_capture.events[0].kind, 'runtime-opaque')
        self.assertEqual(c._zxux_capture.events[0].source, 'RT7')
        report = c._zxux_capture.audit(bytes(c.m.far[:2]))
        self.assertEqual(report['uncovered_bytes'], 0)
        self.assertFalse(report['safe_to_optimize'])

    def test_no_compiler_patch_twice(self):
        c = Mock()
        install(types.SimpleNamespace(Compiler=Mock))
        c.emit('ret')
        self.assertEqual(len(c._zxux_capture.events), 1)


if __name__ == '__main__':
    unittest.main()
