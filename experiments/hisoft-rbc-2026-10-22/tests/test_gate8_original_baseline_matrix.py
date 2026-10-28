"""Verify native size and optimizer disposition of unchanged original BASIC.

These audits are not game publication or runtime proof. Locked external inputs
are required; without them the tests report skips rather than invented passes.
"""
from pathlib import Path
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]


class OriginalGate8Matrix(unittest.TestCase):
    def _check_originals(self, selected):
        required = ('RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
                    'RBC_G8_OPTIMIZER')
        settings = {name: os.environ.get(name) for name in required}
        if not all(settings.values()) or not all(Path(p).is_file() if k == 'RBC_G8_TAPE'
                                                 else Path(p).is_dir()
                                                 for k, p in settings.items()):
            self.skipTest('locked compiler, ROM tape and upstream optimizer required')
        from gate8_full_source_audit import run
        # Exact native sizes come from independent ras/rld links at three
        # process bases. Zero savings is a valid result, not optimizer proof.
        expected = {
            '01-minelay': (9442, 8976, None),
            '07-critical-path-analysis': (11293, 13180, 'original_rt_2117'),
            '16-snap': (8873, 11628, None),
            '23-biorhythms': (6923, 6600, 'original_rt_150b'),
            '48-energy-field': (13754, 13017, None),
            '52-stellar-run': (11726, 13832, None),
            '56-roots': (9667, 9891, None),
        }
        for game, (file_bytes, total_bytes, blocker) in expected.items():
            if game not in selected:
                continue
            with self.subTest(game=game):
                original = (ROOT / 'src/bonus/60-programs' / game / 'BASIC'
                            / (game + '.bas'))
                report = run(original, Path(settings['RBC_G8_CHECKPOINT']),
                             Path(settings['RBC_G8_FRONTEND']),
                             Path(settings['RBC_G8_TAPE']),
                             ROOT / 'src/zx-ux-sdk/rom/48.rom')
                native = report['native_whole_source_baseline']
                self.assertTrue(native['native_whole_source_baseline_linked'])
                self.assertTrue(native['native_image_byte_exact'])
                self.assertTrue(native['all_source_relocations_verified'])
                self.assertEqual(native['native_source_bases'], 3)
                self.assertEqual(native['native_file_bytes'], file_bytes)
                self.assertEqual(native['native_total_bytes'], total_bytes)
                self.assertLessEqual(max(file_bytes, total_bytes), 14000)
                candidate = native['native_whole_optimizer_candidate']
                self.assertFalse(native['native_behavior_verified'])
                self.assertFalse(report['gate8_complete'])
                self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
                self.assertFalse(candidate['native_behavior_verified'])
                if blocker is not None:
                    self.assertFalse(candidate['native_candidate_link_verified'])
                    self.assertIn(blocker, candidate['blocker'])
                    self.assertIn('protected resource boundary', candidate['blocker'])
                else:
                    self.assertTrue(candidate['native_candidate_link_verified'])
                    self.assertTrue(candidate['candidate_byte_identical'])
                    self.assertEqual(candidate['candidate_file_bytes_saved'], 0)
                    self.assertEqual(candidate['candidate_total_bytes_saved'], 0)

    def test_smaller_original_native_baselines(self):
        self._check_originals(('01-minelay', '16-snap', '23-biorhythms',
                               '56-roots'))

    def test_larger_original_native_baselines(self):
        self._check_originals(('07-critical-path-analysis', '48-energy-field',
                               '52-stellar-run'))


if __name__ == '__main__':
    unittest.main()
