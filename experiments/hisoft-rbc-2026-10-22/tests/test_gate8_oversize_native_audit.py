"""Original BAS above passive 14 KB: retain checked native measurements, never admit."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]


class OversizeNativeSourceAuditTests(unittest.TestCase):
    def original(self, game):
        keys = ('RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
                'RBC_G8_OPTIMIZER')
        paths = [os.environ.get(k) for k in keys]
        if not all(paths):
            self.skipTest('requires locked HiSoft, compiler tape and upeepz80 sources')
        from gate8_full_source_audit import run
        source = ROOT / 'src/bonus/60-programs' / game / 'BASIC' / (game + '.bas')
        return run(source, Path(paths[0]), Path(paths[1]), Path(paths[2]),
                   ROOT / 'src/zx-ux-sdk/rom/48.rom')

    def test_oversized_passive_stellar_run_and_energy_field_fit_native_baseline(self):
        for game, passive_file, passive_total, native_file, native_total in (
                ('48-energy-field', 14111, 13355, 13754, 13017),
                ('52-stellar-run', 12083, 14170, 11726, 13832)):
            with self.subTest(game=game):
                report = self.original(game)
                self.assertEqual((report['file'], report['total']),
                                 (passive_file, passive_total))
                self.assertGreater(max(passive_file, passive_total), 14000)
                self.assertFalse(report['passive_within_default_limit'])
                self.assertFalse(report['passive_loader_admitted'])
                whole = report['native_whole_source_baseline']
                self.assertTrue(whole['native_whole_source_baseline_linked'])
                self.assertTrue(whole['native_image_byte_exact'])
                self.assertTrue(whole['all_source_relocations_verified'])
                self.assertEqual(whole['native_source_bases'], 3)
                self.assertEqual((whole['native_file_bytes'],
                                  whole['native_total_bytes']),
                                 (native_file, native_total))
                self.assertLessEqual(max(native_file, native_total), 14000)
                candidate = whole['native_whole_optimizer_candidate']
                self.assertTrue(candidate['native_candidate_link_verified'])
                self.assertTrue(candidate['candidate_byte_identical'])
                self.assertEqual(candidate['candidate_file_bytes_saved'], 0)
                self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
                self.assertFalse(candidate['native_behavior_verified'])
                self.assertFalse(whole['ssx_loader_or_entry_verified'])
                self.assertFalse(report['gate8_complete'])

    def test_evolution_three_is_still_oversized_after_full_native_relink(self):
        report = self.original('46-evolution-3')
        self.assertEqual((report['file'], report['total']), (14432, 14350))
        self.assertFalse(report['passive_within_default_limit'])
        self.assertFalse(report['passive_loader_admitted'])
        whole = report['native_whole_source_baseline']
        self.assertFalse(whole['native_whole_source_baseline_linked'])
        self.assertIn('native source baseline exceeds default memory limit',
                      whole['blocker'])
        for field in ('file=', 'image=', 'bss=', 'stack=', 'total=', 'limit=14000'):
            self.assertIn(field, whole['blocker'])
        self.assertFalse(whole['full_program_optimized'])
        self.assertFalse(whole['native_behavior_verified'])
        self.assertFalse(report['gate8_complete'])


if __name__ == '__main__':
    unittest.main()
