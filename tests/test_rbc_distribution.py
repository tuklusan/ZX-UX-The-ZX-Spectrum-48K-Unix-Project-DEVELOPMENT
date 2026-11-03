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
        source = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections/60-programs'
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
                self.assertFalse((target / 'assets/rbc-bin/60-programs/tzx' / (title + '.tzx')).exists())
                continue
            accepted.append(title)
            self.assertEqual(original_ssx.read_bytes(),
                             (target / 'assets/rbc-bin/60-programs/ssx' / original_ssx.name).read_bytes())
            data = original_ssx.read_bytes()
            info = rld.parse_ssx(data)
            self.assertLessEqual(max(rtap.need(data), len(data)), 14000)
            label = basicpack.tape_name(title)
            self.assertNotIn(label, labels)
            labels.add(label)
            tape = (target / 'assets/rbc-bin/60-programs/tzx' / (title + '.tzx')).read_bytes()
            _, blocks = rtap.tzx_blocks(tape)
            self.assertEqual(len(blocks), 2)
            self.assertEqual(blocks[0][1], rtap.records(data, label)[0])
            self.assertEqual(blocks[1][1], rtap.records(data, label)[1])
        self.assertEqual(len(accepted), 34)
        self.assertEqual({p.stem for p in (target / 'assets/rbc-bin/60-programs/ssx').glob('*.ssx')}, set(accepted))
        self.assertEqual({p.stem for p in (target / 'assets/rbc-bin/60-programs/tzx').glob('*.tzx')}, set(accepted))

    def test_other_collection_and_failed_game(self):
        original = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections/60-programs/53-russian-roulette'
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
            self.assertEqual((stage / 'assets/rbc-bin/demo/ssx/01-sample.ssx').read_bytes(),
                             (original / 'bin/53-russian-roulette.ssx').read_bytes())
            (game / 'bin/01-sample.ssx').unlink()
            (game / 'bin/README.md').write_text('Rejected input\n')
            stage2 = Path(temp) / 'dist2'
            basicpack.package(source, stage2)
            self.assertFalse((stage2 / 'assets/rbc-bin/demo/tzx/01-sample.tzx').exists())

    def test_multiple_original_collections(self):
        original = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections/60-programs/53-russian-roulette'
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'src'
            archive = source / 'assets/basic-src/original-sinclair-basic-collections'
            for name in ('first-set', 'second-set'):
                game = archive / name / '01-sample'
                (game / 'BASIC').mkdir(parents=True)
                (game / 'bin').mkdir()
                for suffix in ('.bas', '.tzx'):
                    (game / 'BASIC' / ('01-sample' + suffix)).write_bytes(
                        (original / 'BASIC' / ('53-russian-roulette' + suffix)).read_bytes())
                (game / 'bin/01-sample.ssx').write_bytes(
                    (original / 'bin/53-russian-roulette.ssx').read_bytes())
            (archive / 'not-yet-compiled/01-pending/BASIC').mkdir(parents=True)
            (archive / 'not-yet-compiled/01-pending/BASIC/Only.tzx').write_bytes(b'old tape')
            self.assertEqual(basicpack.package(source, Path(temp) / 'dist'), 3)
            for name in ('first-set', 'second-set'):
                self.assertTrue((Path(temp) / 'dist/assets/rbc-bin' / name / 'ssx/01-sample.ssx').is_file())
            self.assertTrue((Path(temp) / 'dist/assets/basic-src/not-yet-compiled/01-pending/Only.tzx').is_file())
            self.assertFalse(list((Path(temp) / 'dist/assets/rbc-bin/not-yet-compiled/ssx').glob('*.ssx')))

    def test_original_filenames_and_pending_programs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'src/assets/basic-src/original-sinclair-basic-collections'
            ravine = root / 'Granada-Publishing/01-ravine/BASIC'
            ravine.mkdir(parents=True)
            (ravine / 'Ravine.bas').write_text('10 PRINT "RAVINE"\n')
            (ravine / 'Ravine.tzx').write_bytes(b'original Granada tape')
            show = root / 'www.thespectrumshow.net/14-outlander/BASIC'
            show.mkdir(parents=True)
            (show / 'Outlander.tzx').write_bytes(b'original Spectrum Show tape')
            stage = Path(temp) / 'dist'
            self.assertEqual(basicpack.package(Path(temp) / 'src', stage), 2)
            self.assertEqual((stage / 'assets/basic-src/Granada-Publishing/01-ravine/Ravine.bas').read_text(),
                             '10 PRINT "RAVINE"\n')
            self.assertEqual((stage / 'assets/basic-src/www.thespectrumshow.net/14-outlander/Outlander.tzx').read_bytes(),
                             b'original Spectrum Show tape')
            self.assertFalse(list((stage / 'assets/rbc-bin/Granada-Publishing/ssx').glob('*.ssx')))
            self.assertFalse(list((stage / 'assets/rbc-bin/www.thespectrumshow.net/tzx').glob('*.tzx')))

    def test_granada_and_other_accepted_packages(self):
        archive = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections'
        dist = ROOT / 'dist'
        counts = {}
        for collection in ('Granada-Publishing', 'numerical-analysis', 'www.thespectrumshow.net'):
            original = archive / collection
            accepted = sorted(p for p in original.iterdir()
                              if (p / 'bin' / (p.name + '.ssx')).is_file())
            counts[collection] = len(accepted)
            self.assertEqual({p.stem for p in (dist / 'assets/rbc-bin' / collection / 'ssx').glob('*.ssx')},
                             {p.name for p in accepted})
            self.assertEqual({p.stem for p in (dist / 'assets/rbc-bin' / collection / 'tzx').glob('*.tzx')},
                             {p.name for p in accepted})
            for game in accepted:
                with self.subTest(game=game.name):
                    source = game / 'BASIC'
                    binary = game / 'bin' / (game.name + '.ssx')
                    data = binary.read_bytes()
                    self.assertEqual(data, (dist / 'assets/rbc-bin' / collection / 'ssx' / binary.name).read_bytes())
                    self.assertLessEqual(max(len(data), rtap.need(data)), 14000)
                    tape = dist / 'assets/rbc-bin' / collection / 'tzx' / (game.name + '.tzx')
                    _, blocks = rtap.tzx_blocks(tape.read_bytes())
                    self.assertEqual([part[1] for part in blocks],
                                     list(rtap.records(data, basicpack.tape_name(game.name))))
                    originals = [p for p in source.iterdir() if p.suffix.lower() in ('.bas', '.tzx')]
                    for original_file in originals:
                        released = dist / 'assets/basic-src' / collection / game.name / original_file.name
                        self.assertEqual(original_file.read_bytes(), released.read_bytes())
                    selected = game / 'bin' / (game.name + '.source')
                    names = [selected.read_text().strip()] if selected.exists() else [p.name for p in originals
                                                                                       if p.suffix.lower() == '.bas']
                    self.assertEqual(len(names), 1)
                    self.assertEqual({p.name for p in (dist / 'assets/rbc-src' / collection / game.name).glob('*.bas')},
                                     set(names))
        self.assertGreaterEqual(counts['Granada-Publishing'], 6)
        self.assertGreaterEqual(counts['numerical-analysis'], 12)
        self.assertGreaterEqual(counts['www.thespectrumshow.net'], 28)

    def test_native_captures_in_both_engines(self):
        from PIL import Image
        dist = ROOT / 'dist'
        images = dist / 'screenshots/rbc-bin'
        for collection in ('60-programs', 'Granada-Publishing', 'numerical-analysis',
                           'www.thespectrumshow.net'):
            binaries = {p.stem for p in (dist / 'assets/rbc-bin' / collection / 'ssx').glob('*.ssx')}
            for engine in ('rvm', 'fuse'):
                folder = images / engine / collection
                self.assertEqual({p.stem for p in folder.glob('*.png')}, binaries)
                for name in binaries:
                    with Image.open(folder / (name + '.png')) as png:
                        png.verify()
                self.assertTrue((images / engine / 'index.html').is_file())

    def test_selected_source_with_multiple_originals(self):
        original = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections/60-programs/53-russian-roulette'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            game = path / 'src/assets/basic-src/original-sinclair-basic-collections/demo/01-sample'
            (game / 'BASIC').mkdir(parents=True)
            (game / 'bin').mkdir()
            for name in ('First.bas', 'Second.bas'):
                (game / 'BASIC' / name).write_text('10 PRINT "OK"\n')
            (game / 'BASIC/First.tzx').write_bytes(b'original tape')
            (game / 'bin/01-sample.ssx').write_bytes((original / 'bin/53-russian-roulette.ssx').read_bytes())
            (game / 'bin/01-sample.source').write_text('Second.bas\n')
            release = path / 'out'
            basicpack.package(path / 'src', release)
            self.assertEqual({p.name for p in (release / 'assets/rbc-src/demo/01-sample').iterdir()},
                             {'Second.bas'})
            self.assertEqual({p.name for p in (release / 'assets/basic-src/demo/01-sample').iterdir()},
                             {'First.bas', 'Second.bas', 'First.tzx'})

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
