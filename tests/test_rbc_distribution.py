"""Standalone RBC and BASIC release checks; never modify archival game inputs."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'src/zx-ux-sdk'
sys.path[:0] = [str(SDK), str(SDK / 'tools')]
import basicpack
import rld
import rtap


class BasicDistribution(unittest.TestCase):
    def test_accepted_results_and_originals(self):
        source = ROOT / 'src/bonus/60-programs'
        target = ROOT / 'dist'
        games = sorted(source.glob('[0-9][0-9]-*'))
        self.assertEqual(len(games), 60)
        accepted = []
        labels = set()
        for game in games:
            title = game.name
            base = game / 'BASIC'
            for suffix in ('.bas', '.tzx'):
                original = base / (title + suffix)
                self.assertTrue(original.is_file())
                self.assertEqual(original.read_bytes(),
                                 (target / 'assets/basic-src/60-programs' / title / original.name).read_bytes())
            for png in (base / 'SCREENSHOTS').glob('*.png'):
                self.assertEqual(png.read_bytes(),
                                 (target / 'screenshots/basic-original/60-programs' / title / png.name).read_bytes())
            original_ssx = game / 'bin' / (title + '.ssx')
            readme = game / 'bin/README.md'
            self.assertNotEqual(original_ssx.is_file(), readme.is_file())
            if readme.is_file():
                self.assertFalse((target / 'assets/basic-bin/60-programs/tzx' / (title + '.tzx')).exists())
                continue
            accepted.append(title)
            self.assertEqual(original_ssx.read_bytes(),
                             (target / 'assets/basic-bin/60-programs/ssx' / original_ssx.name).read_bytes())
            data = original_ssx.read_bytes()
            info = rld.parse_ssx(data)
            self.assertLessEqual(max(rtap.need(data), len(data)), 14000)
            label = basicpack.tape_name(title)
            self.assertNotIn(label, labels)
            labels.add(label)
            tape = (target / 'assets/basic-bin/60-programs/tzx' / (title + '.tzx')).read_bytes()
            _, blocks = rtap.tzx_blocks(tape)
            self.assertEqual(len(blocks), 2)
            self.assertEqual(blocks[0][1], rtap.records(data, label)[0])
            self.assertEqual(blocks[1][1], rtap.records(data, label)[1])
        self.assertEqual(len(accepted), 34)
        self.assertEqual({p.stem for p in (target / 'assets/basic-bin/60-programs/ssx').glob('*.ssx')}, set(accepted))
        self.assertEqual({p.stem for p in (target / 'assets/basic-bin/60-programs/tzx').glob('*.tzx')}, set(accepted))

    def test_other_collection_and_failed_game(self):
        original = ROOT / 'src/bonus/60-programs/53-russian-roulette'
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'source'
            game = source / 'assets/basic-src/demo/01-sample'
            (game / 'BASIC').mkdir(parents=True)
            (game / 'bin').mkdir()
            (game / 'BASIC/01-sample.bas').write_bytes((original / 'BASIC/53-russian-roulette.bas').read_bytes())
            (game / 'BASIC/01-sample.tzx').write_bytes((original / 'BASIC/53-russian-roulette.tzx').read_bytes())
            (game / 'bin/01-sample.ssx').write_bytes((original / 'bin/53-russian-roulette.ssx').read_bytes())
            stage = Path(temp) / 'dist'
            self.assertEqual(basicpack.package(source, stage), 1)
            self.assertEqual((stage / 'assets/basic-bin/demo/ssx/01-sample.ssx').read_bytes(),
                             (original / 'bin/53-russian-roulette.ssx').read_bytes())
            (game / 'bin/01-sample.ssx').unlink()
            (game / 'bin/README.md').write_text('Rejected input\n')
            stage2 = Path(temp) / 'dist2'
            basicpack.package(source, stage2)
            self.assertFalse((stage2 / 'assets/basic-bin/demo/tzx/01-sample.tzx').exists())

    def test_both_clis_offline(self):
        packaged = ROOT / 'dist/sdk/bin'
        self.assertTrue((packaged / 'rbc').is_file())
        self.assertTrue((packaged / 'py/rbc/driver.py').is_file())
        for args, env in (
            ([str(SDK / 'bin/rbc'), '--help'], None),
            (['-m', 'rbc', '--help'], dict(os.environ, PYTHONPATH=str(SDK))),
            ([str(packaged / 'rbc'), '--help'], None),
            (['-m', 'rbc', '--help'], dict(os.environ, PYTHONPATH=str(packaged / 'py'))),
        ):
            result = subprocess.run([sys.executable, '-B'] + args, cwd=Path(tempfile.gettempdir()),
                                    env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--max', result.stdout)


if __name__ == '__main__':
    unittest.main()
