"""Source-owned native DEF FN skips, preserved without filling executable gaps."""
from pathlib import Path
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]


class NativeDefFnSourceTests(unittest.TestCase):
    def test_original_skipped_fn_parameters_are_protected_native_data(self):
        required = tuple(os.environ.get(k) for k in (
            'RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
            'RBC_G8_OPTIMIZER'))
        if not all(required):
            self.skipTest('exact original compiler, frontend and optimizer required')
        from gate8_full_source_audit import run
        for game, reserved in (('43-dogfight', 10), ('49-drag-racer', 40)):
            with self.subTest(game=game):
                source = (ROOT / 'src/bonus/60-programs' / game /
                          'BASIC' / (game + '.bas'))
                report = run(source, Path(required[0]), Path(required[1]),
                             Path(required[2]), ROOT / 'src/zx-ux-sdk/rom/48.rom')
                original = report['audits'][0]
                # The slots are the original compiler's unwritten parameter
                # storage; their bytes must be accounted for, not decoded.
                self.assertEqual(original['uncovered_bytes'], 0)
                source_map = report['native_runtime_handoff']
                self.assertTrue(source_map['runtime_handoff_verified'])
                self.assertEqual(source_map['normalized_source_gaps'], 0)
                self.assertEqual(source_map['normalized_source_overlaps'], 0)
                self.assertEqual(source_map['normalized_source_mismatches'], 0)
                self.assertGreaterEqual(source_map['source_kind_bytes']['inline-data'], reserved)
                whole = report['native_whole_source_baseline']
                self.assertTrue(whole['native_whole_source_baseline_linked'])
                self.assertTrue(whole['native_image_byte_exact'])
                self.assertTrue(whole['all_source_relocations_verified'])
                self.assertEqual(whole['native_source_bases'], 3)
                self.assertEqual(whole['native_whole_optimizer_candidate']
                                 ['native_baseline_source_reassembled'], True)
                self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()
