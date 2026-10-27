"""Verify the protected numeric USR/VAL guard has its own native source."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_guarded_val import (guarded_val_assembly,
                                      verify_native_guarded_val)
from spectrum_runtime import guarded_val_bytes


class GuardedValNative(unittest.TestCase):
    def test_complete_native_source_matches_original_bytes(self):
        report = verify_native_guarded_val(ras, rld)
        self.assertEqual(report['runtime_bytes'], 122)
        self.assertEqual(report['native_relocations'], 0)
        self.assertTrue(report['native_verified'])

    def test_source_has_explicit_boundaries_not_machine_code_dump(self):
        source = guarded_val_assembly()
        self.assertIn('rbc_val_scan:', source)
        self.assertIn('rbc_val_blocked:', source)
        self.assertIn('jp $35de', source)
        self.assertIn('ld hl,($5c7b)', source)
        self.assertNotIn('defb ', source.lower())
        self.assertEqual(len(guarded_val_bytes()), 122)


if __name__ == '__main__':
    unittest.main()
