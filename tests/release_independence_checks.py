"""Static and source-collection gates for standalone v1 release.

No old SDK, old kernel, or historical executable format is required.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / 'programs/c48'
RUNS = ROOT / 'sdk/tests/runs.json'


class IndependenceChecks(unittest.TestCase):
    def test_checked_in_source_for_all_sessions(self):
        runs = json.loads(RUNS.read_text(encoding='utf-8'))
        self.assertEqual(len(runs), 73)
        base = set()
        for name, entry in runs.items():
            program = entry.get('src', name.split(':')[0])
            source = CORPUS / entry['dir'] / (program + '.c')
            self.assertTrue(source.is_file(), str(source))
            base.add((entry['dir'], program))
        self.assertEqual(len(base), 56)

    def test_v1_goldens_cover_all_sessions(self):
        runs = json.loads(RUNS.read_text(encoding='utf-8'))
        expected = json.loads((ROOT / 'sdk/tests/v1-screens.json').read_text(encoding='utf-8'))
        self.assertEqual(set(runs), set(expected))
        self.assertEqual(len(expected), 73)
        for name, proof in expected.items():
            self.assertEqual(len(proof['sha256']), 64, name)
            self.assertTrue(all(c in '0123456789abcdef' for c in proof['sha256']), name)
            self.assertIn(proof['state'].split(' ')[0], ('exit', 'input', 'frames'), name)

    def test_release_uses_only_checked_in_programs(self):
        runner = (ROOT / 'tools/release_v1.py').read_text(encoding='utf-8')
        cassette = (ROOT / 'tools/mktapes.py').read_text(encoding='utf-8')
        simulator = (ROOT / 'tests/ssxrun.py').read_text(encoding='utf-8')
        for text in (runner, cassette, simulator):
            self.assertNotIn('obsolete-sdk/', text)
            self.assertNotIn('C48SDK', text)
            self.assertNotIn('zx-ux-c48-sdk', text)
        self.assertNotIn("add_argument('--sdk'", runner)
        self.assertIn('validate_boot_proof', runner)
        self.assertIn('tools/lm_v1.py', runner)
        self.assertIn('tools/mktapes.py', runner)
        self.assertIn('sdk/tests/vm_checks.py', runner)

    def test_format_and_mandatory_gate(self):
        self.assertTrue((ROOT / 'programs/c48/ailmzx48/ailmzx48.c').is_file())
        self.assertTrue((ROOT / 'tests/fuse_boot.py').is_file())
        self.assertTrue((ROOT / 'tools/fuse_release_gate.py').is_file())
        self.assertTrue((ROOT / 'tools/mkrelease.py').is_file())
        text = (ROOT / 'sdk/rcc/driver.py').read_text(encoding='utf-8')
        # The CLI contract is exercised by the C48 verifier. Do not tie
        # the release check to one spelling of the driver's output expression.
        self.assertIn("'.ssx'", text)
        self.assertIn("'.sso'", text)
        self.assertIn('os.path.samefile(src, target)', text)


if __name__ == '__main__':
    unittest.main()
