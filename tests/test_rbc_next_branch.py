"""Check source-backed HiSoft integer NEXT branches and native releases."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'src/zx-ux-sdk'
sys.path[:0] = [str(SDK), str(SDK / 'rbc')]
from symbolic_capture import Emission
from symbolic_patch_binding import _bind_original_next_branches, PatchBindingError
import rld


class NativeNextBranches(unittest.TestCase):
    def test_original_integer_next_is_typed_without_changing_bytes(self):
        image = b'\x7c\xee\x80\xf2\x01\x00'
        emitted = (
            Emission(0, 'instruction', 'ld a,h; xor $80; defb $F2',
                     image[:4], source_site='st_next:1904'),
            Emission(4, 'relocation', '1', image[4:], 1,
                     source_site='st_next:1908'),
        )
        bound = _bind_original_next_branches(emitted, image)
        self.assertEqual([item.kind for item in bound],
                         ['instruction', 'opcode', 'relocation'])
        self.assertEqual(b''.join(item.data for item in bound), image)
        self.assertEqual(bound[1].source, 'jp p,nn')
        self.assertEqual(bound[2], emitted[1])
        for damaged in (
            emitted[:1],
            (replace(emitted[0], data=b'\x7c\xee\x80\xc2'), emitted[1]),
            (emitted[0], replace(emitted[1], position=5)),
            (emitted[0], replace(emitted[1], source_site='st_other:1908')),
            (emitted[0], replace(emitted[1], symbol_offset=9)),
        ):
            with self.subTest(damaged=damaged), self.assertRaises(PatchBindingError):
                _bind_original_next_branches(damaged, image)

    def test_native_next_and_existing_binary(self):
        collection = (ROOT / 'src/assets/basic-src/original-sinclair-basic-collections'
                      / 'numerical-analysis')
        with tempfile.TemporaryDirectory() as temporary:
            for name in ('01-bisect', '03-cholesky', '20-whetstone'):
                game = collection / name
                sources = list((game / 'BASIC').glob('*.bas'))
                self.assertEqual(len(sources), 1, game.name)
                result = Path(temporary) / (game.name + '.ssx')
                compiled = subprocess.run(
                    [sys.executable, '-B', str(SDK / 'bin/rbc'),
                     str(sources[0]), '-o', str(result)],
                    capture_output=True, text=True, timeout=90)
                with self.subTest(game=game.name):
                    self.assertEqual(compiled.returncode, 0, compiled.stderr)
                    self.assertTrue(result.is_file())
                    rld.parse_ssx(result.read_bytes())
                    old = game / 'bin' / (game.name + '.ssx')
                    if old.exists():
                        self.assertEqual(result.read_bytes(), old.read_bytes())


if __name__ == '__main__':
    unittest.main()
