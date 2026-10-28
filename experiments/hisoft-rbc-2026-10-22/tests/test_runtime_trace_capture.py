"""Verify the passive compiler bridge retains runtime output bytes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_capture import install


class CPU:
    def __init__(self):
        self.mem = bytearray(65536)
        self.trace = None

    def wb(self, addr, value):
        self.mem[addr & 65535] = value & 255


class Machine:
    def __init__(self):
        self.de_flags = 0
        self.p = {'direct': True, 'staging': 0x9000}
        self.cpu = CPU()
        self.far = bytearray(64)

    def run_emitter(self, n, pc, counting, code_base):
        self.cpu.trace(0x7101) if self.cpu.trace else None
        self.cpu.wb(0x9000 + pc, 0xc9)
        self.cpu.wb(0x9000 + pc + 1, 0)
        if not counting:
            self.far[pc:pc + 2] = self.cpu.mem[0x9000 + pc:0x9000 + pc + 2]
        return pc + 2


class Compiler:
    def __init__(self):
        self.m = Machine()
        self.far = self.m.far
        self.pc = 0
        self.storing = True
        self.reset()

    def reset(self):
        self.pc = 0

    def emit_byte(self, value):
        self.far[self.pc] = value & 255
        self.pc += 1

    def emit_word(self, value):
        self.emit_byte(value & 255)
        self.emit_byte(value >> 8)

    def emit_word_reloc(self, value):
        self.emit_word(value)

    def emit_bytes(self, value):
        self.far[self.pc:self.pc + len(value)] = value
        self.pc += len(value)

    def emit(self, source, *values):
        self.emit_bytes(b'\xc9')

    def emit_opcode(self, source):
        self.emit_bytes(b'\xc3')


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(SimpleNamespace(Compiler=Compiler,
                                rtlib=SimpleNamespace(Machine=Machine)))

    def test_live_emitter_copy_is_identical_and_untyped(self):
        c = Compiler()
        actual = c.m.run_emitter(9, 0, False, 0x6000)
        self.assertEqual(actual, 2)
        self.assertEqual(c.far[:2], b'\xc9\0')
        report = c._zxux_capture.audit(bytes(c.far[:2]))
        self.assertEqual(report['runtime_emitter_traces'], 1)
        self.assertEqual(report['runtime_trace_source_pc_count'], 1)
        self.assertEqual(report['runtime_trace_covered_bytes'], 2)
        self.assertEqual(report['runtime_trace_uncovered_bytes'], 0)
        self.assertEqual(report['byte_categories'], {'runtime-opaque': 2})
        self.assertFalse(report['safe_to_optimize'])
        self.assertFalse(c._zxux_capture.runtime_traces[0]['typed_instructions'])

    def test_opaque_emitter_without_producer_writes_cannot_be_complete(self):
        class IncompleteMachine(Machine):
            _zxux_runtime_capture_installed = False
            def run_emitter(self, n, pc, counting, code_base):
                if self.cpu.trace:
                    self.cpu.trace(0x7101)
                self.cpu.wb(0x9000 + pc, 0xc9)
                # The missing second byte is copied from preexisting staging RAM.
                self.far[pc:pc + 2] = self.cpu.mem[0x9000 + pc:0x9000 + pc + 2]
                return pc + 2
        class Child(Compiler):
            _zxux_symbolic_capture_installed = False
            def __init__(self):
                self.m = IncompleteMachine()
                self.far = self.m.far
                self.pc = 0
                self.storing = True
                self.reset()
        install(SimpleNamespace(Compiler=Child,
                                rtlib=SimpleNamespace(Machine=IncompleteMachine)))
        c = Child()
        c.m.run_emitter(9, 0, False, 0x6000)
        audit = c._zxux_capture.audit(bytes(c.far[:2]))
        self.assertEqual(audit['uncovered_bytes'], 0)
        self.assertEqual(audit['runtime_trace_uncovered_bytes'], 1)
        self.assertFalse(audit['runtime_traces_complete'])
        self.assertFalse(audit['complete_byte_trace'])
        self.assertFalse(audit['safe_to_optimize'])

    def test_reviewed_typed_runtime_source_reaches_native_symbolic_link(self):
        from runtime_typed_source import RuntimeStatement
        from symbolic_from_source import from_source
        from symbolic_source_boundaries import inspect_source_boundaries
        from symbolic_emit_sites import inspect_emit_sites
        import ras
        import rld

        c = Compiler()
        def encoder(text):
            return {'ret': b'\xc9', 'defb 0': b'\0'}[text]
        def original_sources(n, start, end, base):
            self.assertEqual((n, start, end, base), (9, 0, 2, 0x6000))
            return ((RuntimeStatement(0, 0x7101, 'instruction', 'ret'),
                     RuntimeStatement(1, 0x7101, 'literal', 'defb 0')),
                    encoder)
        c.m._zxux_typed_runtime_source = original_sources
        self.assertEqual(c.m.run_emitter(9, 0, False, 0x6000), 2)
        events = c._zxux_capture.events
        self.assertEqual([e.kind for e in events], ['instruction', 'inline-data'])
        self.assertEqual(c._zxux_capture.runtime_traces[0]['typed_source_events'], 2)
        self.assertTrue(c._zxux_capture.runtime_traces[0]['typed_instructions'])
        sites = inspect_emit_sites(events)
        self.assertEqual([site.producer_pcs for site in sites],
                         [(0x7101,), (0x7101,)])
        self.assertEqual([site.site for site in sites],
                         ['runtime_pc:28929', 'runtime_pc:28929'])
        image = bytes(c.far[:2])
        typed = inspect_source_boundaries(events, image, 0x6000, 2, 0, encoder)
        self.assertTrue(typed.fully_typed)
        self.assertEqual([s.kind for s in typed.spans], ['instruction', 'inline-data'])
        program = from_source(events, image, 0x6000, 2, 0, encoder)
        obj = ras.assemble_text(program.assembly(), 'runtime-bridge.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'runtime-bridge.sso')], [],
                           entry='start', stack=384)
        self.assertEqual(rld.parse_ssx(ssx)['image'], image)
        self.assertFalse(c._zxux_capture.audit(image)['safe_to_optimize'])

    def test_bad_runtime_source_does_not_fall_back_to_opaque(self):
        from runtime_typed_source import RuntimeStatement, RuntimeSourceError
        c = Compiler()
        c.m._zxux_typed_runtime_source = lambda n, start, end, base: (
            (RuntimeStatement(0, 0x7102, 'instruction', 'ret'),),
            lambda s: b'\xc9')
        with self.assertRaises(RuntimeSourceError):
            c.m.run_emitter(9, 0, False, 0x6000)
        self.assertEqual(c._zxux_capture.events, [])
        self.assertFalse(c._zxux_runtime_emitting)
        self.assertIsNone(c.m.cpu.trace)
        self.assertNotIn('wb', vars(c.m.cpu))

    def test_typed_provider_does_not_skip_counting_mode(self):
        c = Compiler()
        c.m._zxux_typed_runtime_source = lambda *args: self.fail('counting mode queried source')
        c.m.run_emitter(9, 0, True, 0x6000)
        self.assertEqual(c._zxux_capture.events, [])

    def test_counting_mode_does_not_capture_runtime(self):
        c = Compiler()
        c.m.run_emitter(9, 0, True, 0x6000)
        self.assertEqual(c._zxux_capture.runtime_traces, [])
        self.assertEqual(c._zxux_capture.events, [])


if __name__ == '__main__':
    unittest.main()
