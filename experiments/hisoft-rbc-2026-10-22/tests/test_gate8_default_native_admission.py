"""Gate 8 native size gate follows the 14 KB RBC default, not an old trial limit."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

import ras
import rld
from symbolic_z80 import SymbolicError, SymbolicProgram
from gate8_native_whole_optimizer import verify_whole_optimizer_candidate
from typed_whole_pipeline import link_source_pair


class DefaultNativeAdmissionTests(unittest.TestCase):
    def whole_program(self):
        program = SymbolicProgram()
        program.label('start', entry=True)
        program.instruction('ret')
        program.section('data')
        program.label('protected_bytes')
        program.binary(bytes((42,)) * 12400)
        program.section('bss')
        program.reserve(24)
        return program

    def test_symbolic_14k_default_accepts_measured_12_to_14k_baseline(self):
        program = self.whole_program()
        linked, stats = program.optimize(lambda source: source, ras, rld)
        parsed = rld.parse_ssx(linked)
        actual = max(len(linked), len(parsed['image']) + parsed['bss'] + parsed['stack'])
        self.assertGreater(actual, 12000)
        self.assertLessEqual(actual, 14000)
        self.assertEqual(stats['optimized_memory_bytes'], actual)
        self.assertEqual(stats['baseline_memory_bytes'], actual)
        self.assertFalse(stats['optimizer_admitted'])
        self.assertFalse(stats['candidate_behavior_verified'])
        with self.assertRaisesRegex(SymbolicError, 'limit 12000'):
            program.optimize(lambda source: source, ras, rld, max_memory=12000)
        allowed, metrics = program.optimize(lambda source: source, ras, rld,
                                            max_memory=14000)
        self.assertEqual(allowed, linked)
        self.assertEqual(metrics['baseline_memory_bytes'], actual)

    def test_whole_source_candidate_14k_default_and_explicit_12k(self):
        source = self.whole_program().assembly()
        obj = ras.assemble_text(source, 'native-default.s')
        original, *_ = rld.link([rld.Obj(obj, 'native-default.sso')], [],
                                entry='start', stack=384)
        result = verify_whole_optimizer_candidate(source, original, lambda text: text)
        smaller = verify_whole_optimizer_candidate(
            source, original, lambda text: text, max_memory=12000)
        self.assertTrue(result['candidate_within_default_limit'])
        self.assertFalse(smaller['candidate_within_default_limit'])
        self.assertTrue(result['native_baseline_source_reassembled'])
        self.assertTrue(result['native_candidate_link_verified'])
        self.assertFalse(result['optimizer_candidate_admitted_for_publication'])
        self.assertFalse(result['native_behavior_verified'])
        self.assertFalse(result['full_program_optimized'])
        self.assertEqual(result['native_candidate_file_bytes'], len(original))
        info = rld.parse_ssx(original)
        self.assertEqual(result['native_candidate_total_bytes'],
                         len(info['image']) + info['bss'] + info['stack'])

    def test_coverage_of_pipeline_default_without_mutating_the_source(self):
        import inspect
        self.assertEqual(inspect.signature(link_source_pair).parameters['max_memory'].default,
                         14000)


if __name__ == '__main__':
    unittest.main()
