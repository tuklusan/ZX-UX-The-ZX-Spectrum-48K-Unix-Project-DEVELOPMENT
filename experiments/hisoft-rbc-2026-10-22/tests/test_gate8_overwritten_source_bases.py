"""Original compiler cross-base historical emission consistency checks."""
from pathlib import Path
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]


class OriginalHistoricalEmissionTests(unittest.TestCase):
    def test_overwritten_originals_retain_native_full_source(self):
        required = tuple(os.environ.get(k) for k in (
            'RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
            'RBC_G8_OPTIMIZER'))
        if not all(required):
            self.skipTest('requires exact frontend, original compiler and optimizer')
        from gate8_full_source_audit import run
        for game in ('01-minelay', '10-tanx', '25-galaxians'):
            with self.subTest(game=game):
                source = (ROOT / 'src/bonus/60-programs' / game /
                          'BASIC' / (game + '.bas'))
                report = run(source, Path(required[0]), Path(required[1]),
                             Path(required[2]), ROOT / 'src/zx-ux-sdk/rom/48.rom')
                ownership = report['source_byte_ownership']
                self.assertGreater(ownership['source_history_mismatch_variation_bytes'], 0)
                self.assertGreater(ownership['source_overlap_bytes'], 0)
                self.assertFalse(ownership['typed_source_ownership'])
                handoff = report['native_runtime_handoff']
                self.assertTrue(handoff['runtime_handoff_verified'])
                self.assertEqual(handoff['normalized_source_mismatches'], 0)
                self.assertEqual(handoff['normalized_source_overlaps'], 0)
                native = report['native_whole_source_baseline']
                self.assertTrue(native['native_whole_source_baseline_linked'])
                self.assertTrue(native['native_image_byte_exact'])
                self.assertEqual(native['native_source_bases'], 3)
                candidate = native['native_whole_optimizer_candidate']
                self.assertTrue(candidate['native_baseline_source_reassembled'])
                self.assertTrue(candidate['native_candidate_link_verified'])
                self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
                self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()
