"""Operation-based ROM workspace admission; unrelated BASIC fixtures."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
CK = ROOT / 'build/tmp/rbc-generic-candidate-3/rbc'
FE = ROOT / 'build/tmp/tug-fault-investigation/frontend/upstream-pyhsb'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
TAPE = ROOT / 'build/tmp/hisoft-test-original.tap'
sys.path[:0] = [str(CK), str(STAGE), str(ROOT/'src/zx-ux-sdk')]
from native_long_string_proof import workspace_bytes

READY = all(p.is_file() for p in (CK/'rbc.py', FE/'compiler.py', ROM, TAPE))


@unittest.skipUnless(READY, 'requires rebuilt historical RBC and original HiSoft')
class GenericRomRuntime(unittest.TestCase):
    def test_scalar_literal_and_numeric_emit_distinct_workspace_needs(self):
        import rbc
        sources = (
            ('10 PRINT 42\n', (), 0),
            ('10 LET A$="HI"\n20 PRINT A$\n', (69, 70), 1024),
            ('10 LET Q$=""\n20 FOR I=1 TO 32\n'
             '30 LET Q$=Q$+"X"\n40 NEXT I\n50 PRINT LEN Q$\n',
             (69, 70), 2048),
        )
        with tempfile.TemporaryDirectory() as temp:
            for index, (listing, expected, pool) in enumerate(sources):
                with self.subTest(index=index):
                    path = Path(temp)/f'program-{index}.bas'
                    path.write_text(listing, encoding='ascii')
                    builds, metadata = rbc._compile_three(
                        path, FE, TAPE, ROM, 65367, [], 'strict', False, 1)
                    self.assertEqual(len(builds), 3)
                    self.assertTrue(set(expected).issubset(metadata['rom_runtime_uses']))
                    self.assertEqual(workspace_bytes(
                        metadata['optimized_strings'],
                        metadata['rom_runtime_uses']), pool)
                    self.assertNotIn('original-exocet', str(metadata))


if __name__ == '__main__':
    unittest.main()
