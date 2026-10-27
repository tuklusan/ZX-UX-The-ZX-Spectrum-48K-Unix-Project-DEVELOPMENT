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

    def test_direct_patch_source_is_captured_before_binary_output(self):
        class Native48(Mock):
            _zxux_symbolic_capture_installed = False
            def __init__(self):
                self.m = types.SimpleNamespace(p={'direct': True}, far=None)
                self.counting = False
                self.de_flags = 0
                super().__init__()
                self.m.far = self.far
            def patch(self):
                self.far[1:3] = b'\x34\x12'
        install(types.SimpleNamespace(Compiler=Native48))
        c = Native48()
        self.assertIs(c.far, c.m.far)
        c.emit_opcode('jp nn')
        c.emit_word_reloc(0)
        c.patch()
        self.assertEqual(c.far[:3], b'\xc3\x34\x12')
        events = c._zxux_capture.events
        self.assertEqual([x.kind for x in events],
                         ['opcode', 'relocation', 'direct-write'])
        self.assertEqual(events[-1].source, 'patch')
        report = c._zxux_capture.audit(bytes(c.far[:c.pc]))
        self.assertEqual(report['unresolved_direct_write_bytes'], 2)
        self.assertEqual(report['uncovered_bytes'], 0)
        self.assertEqual(report['changed_after_emit'], 0)
        self.assertFalse(report['safe_to_optimize'])

    def test_traced_ram_rejects_resizing_and_strided_writes_atomically(self):
        from symbolic_capture import TracedRAM
        owner = types.SimpleNamespace(counting=False, de_flags=0,
                                      _zxux_capture=Capture())
        far = TracedRAM(bytes(range(8)), owner)
        initial = bytes(far)
        for key, data in ((slice(1, 3), b'\x10\x20\x30'),
                          (slice(1, 3), b'\x10'),
                          (slice(1, 5, 2), b'\x10\x20')):
            with self.subTest(key=key, data=data):
                with self.assertRaisesRegex(ValueError, 'unresolved'):
                    far[key] = data
                self.assertEqual(bytes(far), initial)
                self.assertEqual(owner._zxux_capture.events, [])
        far[2:4] = b'\xaa\xbb'
        self.assertEqual(len(far), len(initial))
        self.assertEqual(owner._zxux_capture.events[0].data, b'\xaa\xbb')

    def test_traced_ram_rejects_untraced_bytearray_mutators_atomically(self):
        from symbolic_capture import TracedRAM
        owner = types.SimpleNamespace(counting=False, de_flags=0,
                                      _zxux_capture=Capture())
        far = TracedRAM(b'1234', owner)
        initial = bytes(far)
        actions = (lambda: far.append(5), lambda: far.extend(b'56'),
                   lambda: far.insert(1, 5), lambda: far.pop(),
                   lambda: far.remove(49), lambda: far.clear(),
                   lambda: far.reverse(),
                   lambda: far.__delitem__(slice(1, 3)),
                   lambda: far.__iadd__(b'5'), lambda: far.__imul__(2))
        for action in actions:
            with self.subTest(action=action):
                with self.assertRaisesRegex(ValueError, 'unresolved untraced'):
                    action()
                self.assertEqual(bytes(far), initial)
                self.assertEqual(owner._zxux_capture.events, [])
        owner.counting = True
        far.append(53)
        self.assertEqual(bytes(far), b'12345')

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

    def test_out_of_image_emission_cannot_pass_trace(self):
        trace = Capture([Emission(0, 'instruction', 'ret', b'\xc9'),
                         Emission(1, 'binary', 'stray', b'\x76')])
        result = trace.audit(b'\xc9')
        self.assertEqual(result['uncovered_bytes'], 0)
        self.assertEqual(result['changed_after_emit'], 0)
        self.assertEqual(result['out_of_image_emission_bytes'], 1)
        self.assertEqual(result['out_of_image_first'], [1])
        self.assertFalse(result['complete_byte_trace'])

    def test_negative_emission_site_does_not_count_as_coverage(self):
        trace = Capture([Emission(-1, 'binary', 'bad-site', b'\x00\xc9')])
        result = trace.audit(b'\xc9')
        self.assertEqual(result['out_of_image_first'], [-1])
        self.assertFalse(result['complete_byte_trace'])

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

    def test_data_source_is_recorded_without_post_link_dump(self):
        class WithData(Mock):
            _zxux_symbolic_capture_installed = False
            def __init__(self):
                super().__init__()
                self.data_start = 20
                self.data_size = 0
                self.line_no = 80
            @property
            def storing_data(self):
                return self.storing
            def st_data(self):
                base = self.data_start + self.data_size
                self.far[base:base+3] = bytes((0xc3, 0, 0x76))
                self.data_size += 3
        install(types.SimpleNamespace(Compiler=WithData))
        c = WithData()
        c.st_data()
        events = c._zxux_capture.events
        self.assertEqual([x.kind for x in events], ['data-source'])
        self.assertEqual(events[0].position, 20)
        self.assertEqual(events[0].source, 'BASIC line 80 DATA')
        self.assertEqual(events[0].data, b'\xc3\x00\x76')
        self.assertEqual(c.far[20:23], b'\xc3\x00\x76')

    def test_def_fn_parameter_reservations_have_typed_producer(self):
        class FnCompiler(Mock):
            _zxux_symbolic_capture_installed = False
            def __init__(self):
                super().__init__()
                self.unwritten = []
            def st_deffn(self):
                self.emit('ret')
                self.unwritten.append((self.pc, 5))
                self.pc += 5
                self.emit('ret')
                self.unwritten.append((self.pc, 2))
                self.pc += 2
                self.emit('ret')
        install(types.SimpleNamespace(Compiler=FnCompiler))
        c = FnCompiler()
        c.st_deffn()
        slots = [event for event in c._zxux_capture.events
                 if event.source_site == 'st_deffn:unwritten']
        self.assertEqual([(s.position, s.kind, s.source, s.data) for s in slots],
                         [(1, 'inline-data', 'protected:def-fn-param', bytes(5)),
                          (7, 'inline-data', 'protected:def-fn-param', bytes(2))])
        self.assertEqual(c._zxux_capture.audit(bytes(c.far[:c.pc]))['uncovered_bytes'], 0)

    def test_def_fn_rejects_invalid_parameter_extent(self):
        class CorruptFn(Mock):
            _zxux_symbolic_capture_installed = False
            def __init__(self):
                super().__init__()
                self.unwritten = []
            def st_deffn(self):
                self.unwritten.append((127, 5))
        install(types.SimpleNamespace(Compiler=CorruptFn))
        with self.assertRaisesRegex(ValueError, 'untyped bounds'):
            CorruptFn().st_deffn()

    def test_no_compiler_patch_twice(self):
        c = Mock()
        install(types.SimpleNamespace(Compiler=Mock))
        c.emit('ret')
        self.assertEqual(len(c._zxux_capture.events), 1)


if __name__ == '__main__':
    unittest.main()
