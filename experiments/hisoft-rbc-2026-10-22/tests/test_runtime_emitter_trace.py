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

    def test_matching_final_bytes_do_not_hide_staging_rewrites(self):
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as trace:
            m.cpu.trace(0x7234)
            m.cpu.wb(0x9000, 0x00)
            m.cpu.trace(0x7236)
            m.cpu.wb(0x9000, 0xc9)
        report = trace.inspect(0, 1, b'\xc9')
        self.assertEqual(report['changed_after_write'], 0)
        self.assertEqual(report['rewritten_bytes'], 1)
        self.assertFalse(report['fully_observed'])

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

    def test_same_anomaly_count_at_different_output_offsets_is_rejected(self):
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as trace:
            m.cpu.trace(0x7010)
            for i, byte in enumerate((0x21, 0x34, 0x12)):
                m.cpu.wb(0x9000 + i, byte)
        original = bytes((0x21, 0x34, 0x12))
        first = trace.inspect(0, 3, bytes((0x22, 0x34, 0x12)))
        second = trace.inspect(0, 3, bytes((0x21, 0x35, 0x12)))
        for report in (first, second):
            report['routine'] = 7
        self.assertEqual(first['source_write_sites_sha256'],
                         second['source_write_sites_sha256'])
        self.assertEqual(first['changed_after_write'], 1)
        self.assertEqual(second['changed_after_write'], 1)
        self.assertNotEqual(first['source_anomalies_sha256'],
                            second['source_anomalies_sha256'])
        with self.assertRaisesRegex(RuntimeTraceError, 'sites changed'):
            verify_three_runtime_traces([[first], [second], [first]],
                                        [0x6000, 0x6100, 0x6200])
        original_report = trace.inspect(0, 3, original)
        original_report['routine'] = 7
        self.assertEqual(verify_three_runtime_traces(
            [[original_report]] * 3, [0x6000, 0x6100, 0x6200])
                         ['runtime_source_gaps'], ())

    def test_unobserved_native_source_gaps_and_rewrites_stay_explicit(self):
        m = self.make_machine()
        with RuntimeEmitterTrace(m) as trace:
            m.cpu.trace(0x7010)
            m.cpu.wb(0x9000, 0xc9)
            m.cpu.wb(0x9000, 0xc9)
        report = trace.inspect(0, 3, b'\xc9\x11\x22')
        report['routine'] = 11
        stable = verify_three_runtime_traces(
            [[report]] * 3, [0x6000, 0x6100, 0x6200])
        self.assertEqual(stable['runtime_source_gaps'], ({
            'routine': 11, 'output_bytes': 3, 'uncovered_bytes': 2,
            'rewritten_bytes': 1, 'changed_after_write': 0,
            'outside_emitter_bytes': 0, 'untraced_pc_writes': 0},))
        self.assertFalse(report['fully_observed'])
        for key, value in (('rewritten_bytes', 0), ('fully_observed', True)):
            with self.subTest(key=key):
                changed = dict(report, **{key: value})
                with self.assertRaisesRegex(RuntimeTraceError, 'sites changed'):
                    verify_three_runtime_traces([[report], [changed], [report]],
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
