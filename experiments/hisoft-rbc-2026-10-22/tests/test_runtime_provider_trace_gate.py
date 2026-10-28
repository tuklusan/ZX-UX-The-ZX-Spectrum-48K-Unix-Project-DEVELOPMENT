"""A typed runtime provider must not conceal unobserved Z80 staging writes."""
from pathlib import Path
from dataclasses import replace
import sys
import types
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from runtime_typed_source import RuntimeStatement
from symbolic_capture import install
from typed_runtime_bridge import (witnesses_from_compiler_captures,
                                  RuntimeBridgeError, splice_three_runtime_sources)


class CPU:
    def __init__(self):
        self.mem = bytearray(65536)
        self.trace = None

    def wb(self, address, value):
        self.mem[address & 0xffff] = value & 255


class Machine:
    def __init__(self):
        self.p = {'direct': True, 'staging': 0x9000}
        self.de_flags = 0
        self.cpu = CPU()
        self.far = bytearray(16)
        self.extra = None
        self._zxux_typed_runtime_source = None

    def run_emitter(self, number, pc, counting, base):
        self.cpu.trace(0x7000)
        self.cpu.wb(0x9000, 0xc9)
        if self.extra == 'rewrite':
            self.cpu.trace(0x7001)
            self.cpu.wb(0x9000, 0xc9)
        if self.extra == 'outside':
            self.cpu.trace(0x7002)
            self.cpu.wb(0x9001, 0x42)
        self.far[pc] = self.cpu.mem[0x9000]
        return pc + 1


class Compiler:
    def __init__(self):
        self.m = Machine()
        self.far = self.m.far
        self.pc = 0
        self.storing = True
        self.counting = False
        self.de_flags = 0
        self.reset(None)

    def reset(self, source):
        self.pc = 0

    def emit(self, *args):
        pass

    def emit_opcode(self, *args):
        pass

    def emit_word_reloc(self, *args):
        pass

    def emit_word(self, *args):
        pass

    def emit_byte(self, *args):
        pass

    def emit_bytes(self, *args):
        pass


class RuntimeProviderTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install(types.SimpleNamespace(
            Compiler=Compiler, rtlib=types.SimpleNamespace(Machine=Machine)))

    @staticmethod
    def provider(calls):
        def supply(number, start, end, base):
            calls.append((number, start, end, base))
            return ((RuntimeStatement(start, 0x7000, 'instruction', 'ret'),),
                    lambda text: b'\xc9' if text == 'ret' else ())
        return supply

    def test_complete_runtime_source_is_still_admitted_as_typed(self):
        c = Compiler()
        calls = []
        c.m._zxux_typed_runtime_source = self.provider(calls)
        self.assertEqual(c.m.run_emitter(7, 0, 0, 0x6000), 1)
        self.assertEqual(calls, [(7, 0, 1, 0x6000)])
        self.assertEqual([(e.kind, e.source, e.data) for e in
                          c._zxux_capture.events], [('instruction', 'ret', b'\xc9')])
        self.assertTrue(c._zxux_capture.runtime_traces[0]['fully_observed'])
        self.assertTrue(c._zxux_capture.runtime_traces[0]['typed_instructions'])

    def test_unobserved_or_rewritten_staging_bytes_block_provider(self):
        for kind in ('outside', 'rewrite'):
            with self.subTest(kind=kind):
                c = Compiler()
                c.m.extra = kind
                calls = []
                c.m._zxux_typed_runtime_source = self.provider(calls)
                with self.assertRaisesRegex(ValueError, 'complete original writer trace'):
                    c.m.run_emitter(7, 0, 0, 0x6000)
                self.assertEqual(calls, [])
                self.assertEqual(c._zxux_capture.events, [])

    def test_opaque_runtime_remains_opaque_on_incomplete_trace(self):
        c = Compiler()
        c.m.extra = 'outside'
        self.assertEqual(c.m.run_emitter(7, 0, 0, 0x6000), 1)
        self.assertEqual(c._zxux_capture.events[0].kind, 'runtime-opaque')
        self.assertFalse(c._zxux_capture.runtime_traces[0]['fully_observed'])
        self.assertFalse(c._zxux_capture.audit(bytes(c.m.far[:1]))['complete_byte_trace'])

    def test_original_captured_writes_feed_three_pass_native_source(self):
        import ras
        import rld
        from z80asm import asm
        from typed_whole_pipeline import (verify_and_build_with_runtime_sources,
                                          link_source_pair)
        bases = (0x6000, 0x6100, 0x6200)
        captures = []
        groups = []
        images = []
        for base in bases:
            c = Compiler()
            c.m.run_emitter(7, 0, 0, base)
            captures.append(c._zxux_capture)
            groups.append(tuple(c._zxux_capture.events))
            images.append(bytes(c.m.far[:1]))
        statement = RuntimeStatement(0, 0x7000, 'instruction', 'ret')
        sources = (((statement,),),) * 3
        witnesses, reports = witnesses_from_compiler_captures(captures, sources)
        self.assertEqual(witnesses[0][0].writes[0].emitter_pc, 0x7000)
        typed, report = splice_three_runtime_sources(
            groups, images, bases, witnesses, asm, observed_traces=reports)
        self.assertTrue(report['typed_runtime_source_spliced'])
        self.assertEqual(typed[0][0].source, 'ret')
        verified = verify_and_build_with_runtime_sources(
            groups, images, bases, [1] * 3, [0] * 3, asm,
            witnesses, reports)
        plain, candidate, sizes = link_source_pair(verified, ras, rld,
                                                   lambda text: text)
        self.assertEqual(plain, candidate)
        self.assertEqual(rld.parse_ssx(plain)['image'], b'\xc9')
        self.assertTrue(sizes['native_links_verified'])
        self.assertFalse(sizes['native_behavior_verified'])

        changed = replace(captures[1].runtime_sources[0], writes=())
        captures[1].runtime_sources[0] = changed
        with self.assertRaisesRegex(RuntimeBridgeError, 'trace'):
            witnesses_from_compiler_captures(captures, sources)
        with self.assertRaisesRegex(RuntimeBridgeError, 'missing typed statements'):
            witnesses_from_compiler_captures(captures[:2] + [captures[2]],
                                             [sources[0], (), sources[2]])

    def test_runtime_capture_cannot_type_an_unobserved_writer(self):
        captures = []
        for base in (0x6000, 0x6100, 0x6200):
            c = Compiler()
            c.m.extra = 'outside' if base == 0x6100 else None
            c.m.run_emitter(7, 0, 0, base)
            captures.append(c._zxux_capture)
        statement = RuntimeStatement(0, 0x7000, 'instruction', 'ret')
        with self.assertRaisesRegex(RuntimeBridgeError, 'trace'):
            witnesses_from_compiler_captures(
                captures, (((statement,),),) * 3)


if __name__ == '__main__':
    unittest.main()
