"""Regression checks for the fail-closed target/ABI release gate."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / 'tests/c48/target_gate.py'
spec = importlib.util.spec_from_file_location('c48_target_gate', MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class TargetGateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((ROOT / 'tests/c48/matrix.json').read_text())
        cls.verifier = json.loads((ROOT / 'build/logs/c48-conformance.json').read_text())
        cls.ix = json.loads((ROOT / 'build/logs/ix-abi-proof.json').read_text())

    def test_current_record_is_unresolved(self):
        result = gate.assess(self.matrix, self.verifier, self.ix)
        self.assertIn(1080, result['unresolved'])
        self.assertEqual(result['indexed'], 20)

    def test_matrix_deletion_does_not_pass(self):
        altered = copy.deepcopy(self.matrix)
        altered['rows'].pop()
        with self.assertRaises(ValueError):
            gate.assess(altered, self.verifier, self.ix)

    def test_unsupported_case_does_not_pass(self):
        altered = copy.deepcopy(self.matrix)
        altered['rows'][0]['passing_cases'] = ['invented_case']
        with self.assertRaises(ValueError):
            gate.assess(altered, self.verifier, self.ix)

    def test_missing_witness_does_not_pass(self):
        with self.assertRaises(ValueError):
            gate.assess(self.matrix, self.verifier, {})

    def test_status_change_cannot_replace_env1_proof(self):
        altered = copy.deepcopy(self.matrix)
        for row in altered['rows']:
            if row['paragraph'] == 1080:
                row['status'] = 'supported'
        result = gate.assess(altered, self.verifier, self.ix)
        self.assertIn(1080, result['unresolved'])


if __name__ == '__main__':
    unittest.main()
