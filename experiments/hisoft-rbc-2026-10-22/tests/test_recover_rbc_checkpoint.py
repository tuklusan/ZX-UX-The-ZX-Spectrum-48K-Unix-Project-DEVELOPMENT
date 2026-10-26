"""Rebuild the original RBC code only from checked Git history."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1] / 'stage'
ROOT = STAGE.parents[2]
sys.path.insert(0, str(STAGE))
from recover_rbc_checkpoint import EXPECTED_SHA256, REVISION, git, restore


class HistoricalCheckpointTests(unittest.TestCase):
    def test_original_three_blobs(self):
        for name, expected in EXPECTED_SHA256.items():
            data = git(ROOT, 'show', f'{REVISION}:experiments/hisoft-rbc-2026-10-22/temporary-checkpoint/{name}')
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected)

    def test_rebuild_and_deny_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'checkpoint'
            result = restore(ROOT, output)
            self.assertIn('rbc.py', result)
            self.assertEqual(len((output / 'rbc/font32.bin').read_bytes()), 768)
            self.assertGreaterEqual(len(result), 45)
            with self.assertRaises(FileExistsError):
                restore(ROOT, output)

    def test_reject_unapproved_remote(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(Exception):
                restore(Path(temp), Path(temp) / 'checkpoint')


if __name__ == '__main__':
    unittest.main()
