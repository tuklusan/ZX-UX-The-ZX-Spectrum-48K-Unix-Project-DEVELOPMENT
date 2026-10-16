"""Static and source-collection gates for standalone v1 release.

No old SDK, old kernel, or historical executable format is required.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / 'release/src/assets/c48-src'
RUNS = ROOT / 'tests/sdk/runs.json'


class IndependenceChecks(unittest.TestCase):
    def test_checked_in_source_for_all_sessions(self):
        runs = json.loads(RUNS.read_text(encoding='utf-8'))
        self.assertEqual(len(runs), 74)
        base = set()
        for name, entry in runs.items():
            program = entry.get('src', name.split(':')[0])
            source = CORPUS / entry['dir'] / (program + '.c')
            self.assertTrue(source.is_file(), str(source))
            base.add((entry['dir'], program))
        self.assertEqual(len(base), 57)

    def test_v1_goldens_cover_all_sessions(self):
        runs = json.loads(RUNS.read_text(encoding='utf-8'))
        expected = json.loads((ROOT / 'tests/sdk/v1-screens.json').read_text(encoding='utf-8'))
        self.assertEqual(set(runs), set(expected))
        self.assertEqual(len(expected), 74)
        for name, proof in expected.items():
            self.assertEqual(len(proof['sha256']), 64, name)
            self.assertTrue(all(c in '0123456789abcdef' for c in proof['sha256']), name)
            self.assertIn(proof['state'].split(' ')[0], ('exit', 'input', 'frames'), name)

    def test_release_uses_only_checked_in_programs(self):
        runner = (ROOT / 'release/build/build.py').read_text(encoding='utf-8')
        cassette = (ROOT / 'release/src/zx-ux-sdk/tools/c48build.py').read_text(encoding='utf-8')
        simulator = (ROOT / 'tests/ssxrun.py').read_text(encoding='utf-8')
        for text in (runner, cassette, simulator):
            self.assertNotIn('obsolete-sdk/', text)
            self.assertNotIn('C48SDK', text)
            self.assertNotIn('zx-ux-c48-sdk', text)
        self.assertIn('c48build.build(', runner)
        self.assertIn('shutil.copytree(', runner)
        self.assertIn('turbo_boot_build.create_tzx(', runner)
        self.assertIn('sdkpack.pack(', runner)
        self.assertIn("programs.rglob('*.c')", cassette)
        self.assertIn('rtap.records(', cassette)

    def test_format_and_mandatory_gate(self):
        self.assertFalse((CORPUS / 'runs.json').exists())
        self.assertTrue((ROOT / 'tests/fuse_boot.py').is_file())
        self.assertTrue((ROOT / 'tools/fuse_release_gate.py').is_file())
        self.assertTrue((ROOT / 'release/build/build.py').is_file())
        self.assertTrue((ROOT / 'release/src/zx-ux/rom/48.rom').is_file())
        text = (ROOT / 'release/src/zx-ux-sdk/rcc/driver.py').read_text(encoding='utf-8')
        self.assertIn("'.ssx'", text)
        self.assertIn("'.sso'", text)
        self.assertTrue('os.path.samefile(src, target)' in text or
                        'os.path.samefile(target, src)' in text)


if __name__ == '__main__':
    unittest.main()
