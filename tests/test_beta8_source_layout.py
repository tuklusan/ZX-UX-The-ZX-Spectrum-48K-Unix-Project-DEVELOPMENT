"""Offline distribution layout checks for the beta-0.0.8 source move."""
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
        self.assertEqual(len(files), 64)
        self.assertFalse(any(p.is_symlink() for p in PROGRAMS.rglob('*')))

    def test_program_sources_and_outputs_align(self):
        names = {'maze1982' if p.parent.name == 'examples' and p.stem == 'maze' else p.stem
                 for p in PROGRAMS.rglob('*.c') if p.name != 'seckern.c'}
        self.assertEqual(len(names), 57)
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

    def test_rebuilder_stages_sources_before_compiling(self):
        script = (ROOT / 'release/build/build.py').read_text()
        self.assertIn("corpus = D/'assets/c48-src'", script)
        self.assertIn("shutil.copytree(corpus, B/'dist-new/assets/c48-src')", script)
        self.assertIn("c48build.build(B/'sdk', B/'dist-new/assets/c48-src'", script)
        self.assertIn("(B/'dist-new').rename(D)", script)
        self.assertIn("(B/'dist-old').rename(D)", script)


if __name__ == '__main__':
    unittest.main()
