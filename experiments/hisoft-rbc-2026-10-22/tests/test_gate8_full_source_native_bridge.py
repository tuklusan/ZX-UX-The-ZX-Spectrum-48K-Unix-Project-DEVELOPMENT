"""A real full-program native link is conditional on original Z80 runtime witnesses."""
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(Path(__file__).resolve().parent),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
from z80asm import asm
from gate8_full_source_audit import verify_full_source_native
from test_typed_runtime_bridge import BASES, fixture


class OriginalSourceNativeBridgeTests(unittest.TestCase):
    def compile_inputs(self):
        events, images, witnesses, traces = fixture()
        runs = [SimpleNamespace(code=image, base=base, bss=0)
                for image, base in zip(images, BASES)]
        return events, runs, witnesses, traces

    def test_runtime_remains_untyped_without_original_writer_witness(self):
        events, runs, _, _ = self.compile_inputs()
        report = verify_full_source_native(events, runs, [4] * 3, asm, ras)
        self.assertFalse(report['source_owned'])
        self.assertFalse(report['native_link_verified'])
        self.assertIn('source', report['blocker'])
        self.assertFalse(report['native_behavior_verified'])

    def test_original_writer_witness_is_joined_and_native_linked(self):
        events, runs, witnesses, traces = self.compile_inputs()
        report = verify_full_source_native(
            events, runs, [4] * 3, asm, ras,
            runtime_witnesses=witnesses, runtime_traces=traces)
        self.assertTrue(report['source_owned'])
        self.assertTrue(report['native_link_verified'])
        self.assertTrue(report['typed_runtime_bridge']['typed_runtime_source_spliced'])
        self.assertEqual(report['typed_runtime_bridge']['runtime_source_passes'], 3)
        self.assertFalse(report['native_behavior_verified'])
        self.assertEqual(report['plain_sizes']['baseline_file_bytes'], 27)

    def test_partial_missing_or_changed_witness_cannot_reach_native_link(self):
        events, runs, witnesses, traces = self.compile_inputs()
        bad = list(witnesses)
        bad[1] = (replace(witnesses[1][0], number=28),)
        for kwargs in ({'runtime_witnesses': witnesses},
                       {'runtime_traces': traces},
                       {'runtime_witnesses': bad, 'runtime_traces': traces}):
            with self.subTest(keys=tuple(kwargs)):
                report = verify_full_source_native(
                    events, runs, [4] * 3, asm, ras, **kwargs)
                self.assertFalse(report['source_owned'])
                self.assertFalse(report['native_link_verified'])
                self.assertFalse(report['native_behavior_verified'])


if __name__ == '__main__':
    unittest.main()
