"""Offline C48 distribution layout checks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'release/dist'
PROGRAMS = DIST / 'assets/c48-src'


class Beta8DistributionSourceChecks(unittest.TestCase):
    def test_only_distributed_program_sources_are_used(self):
        self.assertFalse((ROOT / 'release/src/assets/c48-src').exists())
        self.assertTrue(PROGRAMS.is_dir())
        self.assertFalse(PROGRAMS.is_symlink())
        files = sorted(p for p in PROGRAMS.rglob('*') if p.is_file())
        self.assertGreaterEqual(len(files), len(list(PROGRAMS.rglob("*.c"))))
        self.assertFalse(any(p.is_symlink() for p in PROGRAMS.rglob('*')))

    def test_program_sources_and_outputs_align(self):
        def tape_name(p):
            if p.parent.name == 'examples' and p.stem == 'maze':
                return 'maze1982'
            if p.parent.name == 'games' and p.stem == 'maze1982':
                return 'maze1996'
            return p.stem
        sources = [p for p in PROGRAMS.rglob('*.c') if p.name != 'seckern.c']
        names = {tape_name(p) for p in sources}
        self.assertEqual(len(names), len(sources), 'Source tape names collide')
        for suffix in ('ssx', 'tzx'):
            actual = {p.stem for p in (DIST / 'assets/c48-bin' / suffix).glob('*.' + suffix)}
            self.assertEqual(names, actual)

    def test_regression_runners_use_distributed_sources(self):
        for name in ('tests/run_migrated_baseline.py',
                     'tests/ssxrun.py', 'tests/rvm_corpus.py'):
            script = (ROOT / name).read_text()
            self.assertNotIn("'src/assets/c48-src'", script, name)
            self.assertNotIn("'release', 'src', 'assets', 'c48-src'", script, name)
            self.assertIn('c48-src', script, name)

    def test_rebuilder_replaces_dist_from_staged_inputs(self):
        script = (ROOT / 'release/build/build.py').read_text()
        self.assertIn("corpus = D / 'assets/c48-src'", script)
        self.assertIn("shutil.copytree(corpus, stage / 'assets/c48-src')", script)
        self.assertIn("bonus = S / 'bonus'", script)
        self.assertIn("shutil.copytree(bonus, stage / 'bonus')", script)
        self.assertIn("c48build.build(B / 'sdk', stage / 'assets/c48-src'", script)
        self.assertIn("D.rename(B / 'dist-old')", script)
        self.assertIn("stage.rename(D)", script)
        self.assertIn("(B / 'dist-old').rename(D)", script)

    def test_bonus_source_collection_is_outside_dist(self):
        collection = ROOT / 'release/src/bonus/60-programs'
        self.assertTrue(collection.is_dir())
        folders = sorted(p for p in collection.iterdir() if p.is_dir() and p.name[:2].isdigit())
        self.assertEqual(len(folders), 60)
        for folder in folders:
            self.assertTrue((folder / 'BASIC').is_dir(), folder.name)
            self.assertEqual(len(list((folder / 'BASIC').glob('*.bas'))), 1, folder.name)
            self.assertFalse((folder / 'C48').exists(), folder.name)


if __name__ == '__main__':
    unittest.main()
