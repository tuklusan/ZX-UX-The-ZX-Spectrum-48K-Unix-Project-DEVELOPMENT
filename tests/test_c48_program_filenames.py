"""C48 source names are the published executable names, with no hidden aliases."""
from collections import Counter
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'src/assets/c48-src'
BUILDER = ROOT / 'src/zx-ux-sdk/tools/c48build.py'


def load_builder():
    spec = importlib.util.spec_from_file_location('c48_filename_builder', BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class C48SourceNames(unittest.TestCase):
    def test_no_ambiguous_maze_names(self):
        expected = {('examples', 'maze1982.c'), ('games', 'maze1996.c'),
                    ('games', 'maze.c')}
        found = {(p.parent.name, p.name) for p in SOURCES.rglob('maze*.c')}
        self.assertEqual(found, expected)
        sources = [p for p in SOURCES.rglob('*.c') if p.name != 'seckern.c']
        counts = Counter(p.stem for p in sources)
        self.assertTrue(sources)
        self.assertTrue(all(count == 1 for count in counts.values()))
        for category, filename in expected:
            self.assertEqual((SOURCES / category / filename).read_bytes(),
                             (ROOT / 'dist/assets/c48-src' / category / filename).read_bytes())

    def test_release_names_and_gallery_paths(self):
        runs = json.loads((ROOT / 'build/tools/runs.json').read_text())
        self.assertEqual(runs['maze1982']['src'], 'maze1982')
        self.assertEqual(runs['maze1996']['src'], 'maze1996')
        for emulator in ('rvm', 'fuse'):
            gallery = (ROOT / 'dist/screenshots' / emulator / 'index.html').read_text()
            self.assertIn('../../assets/c48-src/examples/maze1982.c', gallery)
            self.assertIn('../../assets/c48-src/games/maze1996.c', gallery)
            self.assertIn('../../assets/c48-src/games/maze.c', gallery)

    def test_builder_rejects_duplicate_names(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for category in ('examples', 'games'):
                source = root / 'sources' / category / 'maze.c'
                source.parent.mkdir(parents=True)
                source.write_text('int main(void) { return 0; }\n')
            fake_rcc = types.ModuleType('rcc')
            fake_rcc.driver = types.ModuleType('driver')
            with patch.dict(sys.modules, {'rtap': types.ModuleType('rtap'),
                                          'rcc': fake_rcc}):
                with self.assertRaisesRegex(RuntimeError, 'Duplicate C48 program name: maze'):
                    load_builder().build(root, root / 'sources', root / 'out')

    def test_builder_outputs_use_unmodified_source_stems(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for category, name in (('examples', 'maze1982'), ('games', 'maze1996'),
                                   ('games', 'maze')):
                path = root / 'sources' / category / (name + '.c')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('int main(void) { return 0; }\n')
            driver = types.ModuleType('driver')
            def compile_one(args):
                Path(args[2]).write_bytes(b'ZXUX')
                return 0
            driver.main = compile_one
            rcc = types.ModuleType('rcc')
            rcc.driver = driver
            rtap = types.ModuleType('rtap')
            rtap.records = lambda code, name: (b'H', b'C')
            rtap.write = lambda path, header, records: Path(path).write_bytes(header)
            with patch.dict(sys.modules, {'rtap': rtap, 'rcc': rcc}):
                total = load_builder().build(root, root / 'sources', root / 'out')
            self.assertEqual(total, 3)
            for name in ('maze', 'maze1982', 'maze1996'):
                self.assertTrue((root / 'out/ssx' / (name + '.ssx')).is_file())
                self.assertTrue((root / 'out/tzx' / (name + '.tzx')).is_file())


if __name__ == '__main__':
    unittest.main()
