"""Runtime source-PC source origin must not change interpreter output."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from runtime_emitter_trace import (RuntimeEmitterTrace, RuntimeTraceError,
                                   verify_three_runtime_traces)


class CPU:
    def __init__(self):
        self.mem = bytearray(65536)
        self.trace = None

    def wb(self, addr, value):
        self.mem[addr & 65535] = value & 255

    def ww(self, addr, value):
        self.wb(addr, value)
        self.wb(addr + 1, value >> 8)


class NativeTrace(unittest.TestCase):
    def make_machine(self, *, direct=True, staging=0x9000):
        return SimpleNamespace(p={'direct': direct, 'staging': staging}, cpu=CPU())

    def test_original_machine_output_and_producer_pcs_unchanged(self):
        m = self.make_machine()
        before = m.cpu.wb
        seen = []
        m.cpu.trace = seen.append
        with RuntimeEmitterTrace(m) as tracing:
            m.cpu.trace(0x7000)
            m.cpu.wb(0x9000, 0xc9)
            m.cpu.trace(0x7003)
            m.cpu.ww(0x9001, 0x3412)
            self.assertEqual(m.cpu.mem[0x9000:0x9003], b'\xc9\x12\x34')
        self.assertEqual(seen, [0x7000, 0x7003])
        self.assertEqual(m.cpu.trace, seen.append)
        self.assertEqual(m.cpu.wb.__func__, before.__func__)
        report = tracing.inspect(0, 3, bytes(m.cpu.mem[0x9000:0x9003]))
        self.assertTrue(report['fully_observed'])
        self.assertFalse(report['typed_instructions'])
        self.assertEqual(report['source_pc_first'], [0x7000, 0x7003])
        self.assertEqual(report['covered_bytes'], 3)

    def test_missing_rewritten_and_escaped_are_reported(self):
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as trace:
            m.cpu.trace(0x7234)
            m.cpu.wb(0x9000, 0)
            m.cpu.wb(0x9000, 1)
            m.cpu.wb(0x9003, 5)
        r = trace.inspect(0, 3, b'\x02\x03\x04')
        self.assertEqual(r['rewritten_bytes'], 1)
        self.assertEqual(r['changed_first'], [0])
        self.assertEqual(r['uncovered_first'], [1, 2])
        self.assertEqual(r['outside_first'], [3])
        self.assertFalse(r['fully_observed'])

    def test_write_without_instruction_site_is_untyped(self):
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as trace:
            m.cpu.wb(0x9000, 0xc9)
        r = trace.inspect(0, 1, b'\xc9')
        self.assertEqual(r['untraced_pc_writes'], 1)
        self.assertFalse(r['fully_observed'])

    def test_normal_hook_restored_after_exception(self):
        m = self.make_machine()
        old_trace = lambda pc: None
        m.cpu.trace = old_trace
        with self.assertRaisesRegex(RuntimeError, 'failure'):
            with RuntimeEmitterTrace(m) as trace:
                m.cpu.trace(0x7777)
                raise RuntimeError('failure')
        self.assertIs(m.cpu.trace, old_trace)
        self.assertNotIn('wb', vars(m.cpu))

    def test_reject_nondirect_and_invalid_output(self):
        with self.assertRaises(RuntimeTraceError):
            RuntimeEmitterTrace(self.make_machine(direct=False))
        with self.assertRaises(RuntimeTraceError):
            RuntimeEmitterTrace(self.make_machine(staging=0))
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as t:
            m.cpu.trace(0x5010)
            m.cpu.wb(0x9000, 1)
        with self.assertRaises(RuntimeTraceError):
            t.inspect(0, 2, b'\x01')
        with self.assertRaises(RuntimeTraceError):
            t.inspect(-1, 0, b'\x01')

    def test_three_bases_check_entire_write_sequence(self):
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as t:
            m.cpu.trace(0x7010)
            m.cpu.wb(0x9000, 0xc9)
        report = t.inspect(0, 1, b'\xc9')
        report['routine'] = 7
        stable = verify_three_runtime_traces([[report]] * 3,
                                             [0x6000, 0x6100, 0x6200])
        self.assertEqual(stable['runtime_emitter_count'], 1)
        self.assertFalse(stable['complete_runtime_symbolic'])
        modified = dict(report, source_write_sites_sha256='different')
        with self.assertRaisesRegex(RuntimeTraceError, 'sites changed'):
            verify_three_runtime_traces([[report], [report], [modified]],
                                        [0x6000, 0x6100, 0x6200])

    def test_only_staging_writes_are_captured(self):
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as t:
            m.cpu.trace(0x7111)
            m.cpu.wb(0x8800, 3)
            m.cpu.wb(0x9000, 4)
        self.assertEqual(t.inspect(0, 1, b'\x04')['staging_write_count'], 1)


if __name__ == '__main__':
    unittest.main()
