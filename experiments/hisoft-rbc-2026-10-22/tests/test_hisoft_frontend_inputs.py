"""Offline fixture checks for the HiSoft tape and canonical fork lock."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from hisoft_frontend_inputs import (CANONICAL_FRONTEND, ORIGIN, REVISION, FRONTEND,
                                    KNOWN_COMPILER, convert_tzx_to_tap,
                                    copy_frontend, git_blob)


class HiSoftFrontendInputs(unittest.TestCase):
    def test_locked_source_tree_has_required_runtime(self):
        self.assertEqual(len(FRONTEND), 11)
        self.assertIn('compiler.py', FRONTEND)
        self.assertIn('z80mini.py', FRONTEND)
        self.assertTrue(all(len(x) == 40 for x in FRONTEND.values()))

    def test_canonical_frontend_fork_and_revision(self):
        self.assertEqual(CANONICAL_FRONTEND,
                         'https://github.com/tuklusan/Python-BASIC-Compiler-for-ZX-Spectrum-Hisoft')
        self.assertEqual(REVISION, '7cc87dafb58fcf5632b7190320dd11c30b4fe961')
        self.assertEqual(ORIGIN,
                         'https://raw.githubusercontent.com/tuklusan/Python-BASIC-Compiler-for-ZX-Spectrum-Hisoft/'
                         + REVISION + '/')

    def test_corrupt_tape_is_not_accepted(self):
        for raw in (b'', b'ZXTape!\x1a\x01\x14',
                    b'ZXTape!\x1a\x01\x14\x10\x00\x00\x10\x00',
                    b'ZXTape!\x1a\x01\x14\x11\x00'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                convert_tzx_to_tap(raw)

    def test_compiler_only_original_when_supplied(self):
        # No test repo embeds commercial compiler bytes; this opt-in path is
        # exercised with the exact user-provided tape at development time.
        import os
        location = os.environ.get('HISOFT_48K_TZX')
        if not location:
            self.skipTest('Set HISOFT_48K_TZX to test the supplied original')
        data = convert_tzx_to_tap(Path(location).read_bytes())
        self.assertGreater(len(data), 11887)
        self.assertTrue(data)

    def test_mismatched_canonical_source_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'source'
            out = Path(tmp) / 'out'
            src.mkdir()
            for name in FRONTEND:
                (src / name).write_bytes(b'wrong source')
            with self.assertRaisesRegex(ValueError, 'canonical frontend Git blob mismatch'):
                copy_frontend(out, src)
            self.assertFalse(out.exists())

    def test_git_blob_uses_correct_git_object_encoding(self):
        self.assertEqual(git_blob(b'test\n'), '9daeafb9864cf43055ae93beb0afd6c7d144bfa4')


if __name__ == '__main__':
    unittest.main()
