#!/usr/bin/env python3
"""C48 test checks."""
import importlib.util
from pathlib import Path
import unittest

GATE = Path(__file__).with_name('c48') / 'coverage_gate.py'
spec = importlib.util.spec_from_file_location('c48_coverage_gate', GATE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class C48ReleaseChecks(unittest.TestCase):
    def fixture(self):
        trace = {'spec_sha256': 'one', 'requirements': [
            {'paragraph_index': i, 'classification': 'required'} for i in range(1, 759)] +
            [{'paragraph_index': 759, 'classification': 'undefined'}]}
        report = {'spec_sha256': 'one', 'backend': 'both',
                  'cases': [], 'summary': {'PASS': 0, 'FAIL': 0, 'ERROR': 0,
                                           'UNTESTED_PARAGRAPHS': 759},
                  'clauses': [{'paragraph_index': i, 'classification':
                               'undefined' if i == 759 else 'required',
                               'status': 'UNTESTED', 'tests': []}
                              for i in range(1, 760)]}
        return trace, report

    def test_missing_required_stops_release(self):
        t, r = self.fixture()
        s = module.assess(t, r)
        self.assertFalse(s['complete'])
        self.assertEqual(s['required_pending'], 758)
        self.assertEqual(s['undefined_pending'], 1)

    def test_all_required_exercised(self):
        t, r = self.fixture()
        for c in r['clauses'][:-1]:
            n = c['paragraph_index']
            c.update(status='EXERCISED', tests=['check_' + str(n)])
            r['cases'].append({'id': 'check_' + str(n), 'backend': 'native',
                               'status': 'PASS', 'paragraphs': [n]})
        r['summary']['PASS'] = 758
        r['summary']['UNTESTED_PARAGRAPHS'] = 1
        self.assertTrue(module.assess(t, r)['complete'])

    def test_bad_case_mapping(self):
        t, r = self.fixture()
        r['clauses'][0].update(status='EXERCISED', tests=['unlinked'])
        with self.assertRaises(ValueError):
            module.assess(t, r)

    def test_bad_reference(self):
        t, r = self.fixture()
        r['cases'].append({'id': 'bad', 'backend': 'native', 'status': 'PASS',
                           'paragraphs': [800]})
        r['summary']['PASS'] = 1
        with self.assertRaises(ValueError):
            module.assess(t, r)

    def test_launcher_calls_gate(self):
        launcher = Path(__file__).resolve().parents[1] / 'tools/release_v1.py'
        self.assertIn("tests/c48/coverage_gate.py", launcher.read_text())

    def test_backend_required(self):
        t, r = self.fixture()
        r['backend'] = 'native'
        with self.assertRaises(ValueError):
            module.assess(t, r)


if __name__ == '__main__':
    unittest.main()
