"""Fail-closed checks for reviewed C48 dispositions and executed assertions."""
import copy
import csv
import json
from pathlib import Path
import unittest

import coverage_gate as gate

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / 'build/logs/c48-conformance.json'


class CoverageReviewChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace = json.loads(gate.TRACE.read_text())
        cls.report = json.loads(REPORT.read_text())
        with gate.REVIEW.open(newline='', encoding='utf-8') as f:
            cls.rows = list(csv.DictReader(f))

    def review(self, report=None, rows=None, outstanding=gate.TARGET_PARAGRAPHS):
        return gate.assess_reviewed(self.trace, report if report is not None else self.report,
                                    rows if rows is not None else self.rows, outstanding)

    def test_valid_review_reports_90_distinct_nonexecuted(self):
        result = self.review()
        self.assertEqual(result['reviewed_nonexecutable'], 90)
        self.assertEqual(result['target_indexed'], 20)
        self.assertEqual(result['required_pending'], 20)
        self.assertFalse(result['complete'])
        self.assertEqual(result['exercised'], 647)
        self.assertEqual(result['undefined_pending'], 2)

    def test_future_release_completion_requires_independent_target_result(self):
        # Only independent_target_status may supply this empty result in CLI.
        result = self.review(outstanding=[])
        self.assertTrue(result['complete'])
        self.assertEqual(result['required_pending'], 0)

    def test_missing_row_rejected(self):
        with self.assertRaises(ValueError):
            self.review(rows=self.rows[:-1])

    def test_duplicate_row_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[1] = rows[0]
        with self.assertRaises(ValueError):
            self.review(rows=rows)

    def test_wrong_clause_hash_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.review(rows=rows)

    def test_missing_disposition_explanation_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['explanation'] = ''
        with self.assertRaises(ValueError):
            self.review(rows=rows)

    def test_misclassification_with_unchanged_counts_rejected(self):
        rows = copy.deepcopy(self.rows)
        a = next(r for r in rows if r['disposition'] == 'documentation_or_governance')
        b = next(r for r in rows if r['disposition'] == 'optional_or_internal_mechanism')
        a['disposition'], b['disposition'] = b['disposition'], a['disposition']
        with self.assertRaises(ValueError):
            self.review(rows=rows)

    def test_governance_mislabeled_target_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['disposition'] = 'target_runtime_or_format'
        with self.assertRaises(ValueError):
            self.review(rows=rows)

    def test_host_architecture_text_must_be_owner_approved(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r['disposition'] == 'host_rcc_architecture_accepted')
        row['explanation'] = 'Some compiler runs on Windows.'
        with self.assertRaises(ValueError):
            self.review(rows=rows)

    def test_unsupported_executed_case_rejected(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r['disposition'] == 'linked_passing_assertion')
        row['linked_case_ids'] = 'invented_case'
        with self.assertRaises(ValueError):
            self.review(rows=rows)

    def test_unexecuted_case_cannot_claim_exercised(self):
        report = copy.deepcopy(self.report)
        row = next(r for r in report['clauses'] if r['paragraph_index'] == 1080)
        row['status'] = 'EXERCISED'
        row['tests'] = ['invented_native_env1_test']
        with self.assertRaises(ValueError):
            self.review(report=report)

    def test_backend_or_result_cannot_be_relabeled(self):
        for field, value in [('backend', 'native'), ('summary', {'PASS': 1146, 'FAIL': 1, 'ERROR': 0})]:
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                report[field] = value
                with self.assertRaises(ValueError):
                    self.review(report=report)

    def test_unknown_target_attestation_rejected(self):
        with self.assertRaises(ValueError):
            self.review(outstanding=[99999])


if __name__ == '__main__':
    unittest.main()
