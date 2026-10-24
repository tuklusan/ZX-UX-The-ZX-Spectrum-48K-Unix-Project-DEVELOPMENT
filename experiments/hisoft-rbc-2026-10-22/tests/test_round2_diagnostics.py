"""RBC corpus diagnostics: true separation of failed conversion and linked mismatch."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from round2_runner import rejected_conversion, outcome_readme


class CorpusDiagnosticTests(unittest.TestCase):
    def test_semantic_difference_identifies_actual_tape_source(self):
        with tempfile.TemporaryDirectory() as work:
            tape = Path(work) / 'game.tzx'
            tape.write_bytes(b'TAPE')
            raw = 'BAS/TZX: Line 125: semantic token difference at byte 8'
            result = rejected_conversion(tape, raw, 'actual-commit', 'SemanticDifference')
            self.assertEqual(result['exit_status'], 1)
            self.assertFalse(result['native_linked'])
            self.assertEqual(result['sha256_input'], hashlib.sha256(b'TAPE').hexdigest())
            self.assertIn('%RBC RBC_TZX_FIDELITY Line: 125 Statement: -', result['stderr'])
            self.assertIn(raw, result['stderr'])
            self.assertNotIn('^', result['stderr'])

    def test_conversion_failure_does_not_pretend_bas_was_compiled(self):
        with tempfile.TemporaryDirectory() as work:
            tape = Path(work) / 'game.tzx'
            tape.write_bytes(b'BAD TAPE')
            result = rejected_conversion(tape, 'TZX checksum wrong', 'r2', 'LosslessConversionError')
            self.assertIn('%RBC RBC_TZX_CONVERSION Line: - Statement: -', result['stderr'])
            other = {'exit_status': 1, 'stderr': '%RBC BAS_NO_LINE_NUMBER Line: - Statement: - bad',
                     'native_linked': False}
            readme = outcome_readme('game', other, result,
                                    {'status': 'unavailable', 'reason': 'one path failed'})
            self.assertIn('BAS_NO_LINE_NUMBER', readme)
            self.assertIn('RBC_TZX_CONVERSION', readme)
            self.assertNotIn('linked 0 bytes', readme)

    def test_linked_pairs_with_difference_report_both_hashes(self):
        bas = {'native_linked': True, 'linked_bytes': 512, 'sha256_output': 'a' * 64,
               'exit_status': 0}
        tzx = {'native_linked': True, 'linked_bytes': 512, 'sha256_output': 'b' * 64,
               'exit_status': 0}
        reason = '%RBC RBC_SSX_DIFFERENCE Line: - Statement: - First differing byte at offset 72'
        text = outcome_readme('game', bas, tzx, {'status': 'mismatch', 'reason': reason})
        self.assertIn('RBC_SSX_DIFFERENCE', text)
        self.assertIn('SHA-256 ' + 'a' * 64, text)
        self.assertIn('SHA-256 ' + 'b' * 64, text)

if __name__ == '__main__':
    unittest.main()
