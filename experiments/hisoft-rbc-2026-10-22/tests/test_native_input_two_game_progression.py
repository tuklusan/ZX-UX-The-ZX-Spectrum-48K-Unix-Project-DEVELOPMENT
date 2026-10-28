"""Original Minelay and Space Traffic input progression, test-only editor.

The published ROM EDITOR path is still blocked. The editor substituted here is
not production safe: canonical ZX-UX tty input is limited to 79 characters.
Do not publish these experimental linked images into any game bin directory.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(Path(__file__).resolve().parent)]
import rld
import rvm
from native_rbc_cli import compile_native
from test_native_input_bridge_candidate import link_candidate
from test_native_oxo_complete_round import text_row

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
GAMES = ROOT / 'src/bonus/60-programs'
READY = all(p.is_file() for p in (
    CHECKPOINT / 'rbc.py', CHECKPOINT / 'font32.bin',
    FRONTEND / 'compiler.py', TAPE, ROM, SYSTEM, FROZEN))

CASES = (
    ('01-minelay', '{WAIT 250}{ENTER}{WAIT 100}{ENTER}{WAIT 150}2{WAIT 100}q',
     1800, 23, 'Press ENTER to start...', 0, 'Score 0', 'maze'),
    ('30-space-traffic', '{WAIT 250}{ENTER}{WAIT 100}{ENTER}',
     1500, 23, 'PRESS ENTER TO START', 5, 'You scored 0 points.', 'gameover'),
)


@unittest.skipUnless(READY, 'checked HiSoft frontend, ROM, and ZX-UX required')
class NativeOriginalInputTwoGameProgression(unittest.TestCase):
    def test_original_listings_advance_through_test_only_input_source(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        font = (CHECKPOINT / 'font32.bin').read_bytes()
        self.assertEqual(len(font), 768)
        with tempfile.TemporaryDirectory(prefix='rbc-two-input-games-') as tmp:
            for (game, keys, frames, intro_row, intro_text,
                 final_row, final_text, name) in CASES:
                with self.subTest(game=game):
                    folder = GAMES / game
                    bas = folder / 'BASIC' / (game + '.bas')
                    tzx = folder / 'BASIC' / (game + '.tzx')
                    published = folder / 'bin' / (game + '.ssx')
                    originals = tuple(p.read_bytes() for p in (bas, tzx, published))
                    asm, obj, reference, proof = compile_native(
                        bas, CHECKPOINT, FRONTEND, TAPE, ROM)
                    self.assertTrue(obj.startswith(b'SSO1'))
                    self.assertEqual(reference, originals[2])
                    self.assertTrue(proof['native_three_base_source_verified'])
                    self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
                    self.assertFalse(proof['optimizer_used'])
                    candidate = link_candidate(asm)
                    self.assertNotEqual(candidate, reference)
                    decoded = rld.parse_ssx(candidate)
                    self.assertEqual(decoded['entry'], 0)
                    self.assertLessEqual(max(len(candidate), len(decoded['image']) +
                                             decoded['bss'] + decoded['stack']), 14000)
                    trial = Path(tmp) / (game + '.ssx')
                    trial.write_bytes(candidate)
                    intro = rvm.run_kernel(trial, keys='', frames=frames,
                                           system=SYSTEM)
                    self.assertEqual(intro.why, 'input', intro.summary())
                    intro_screen, intro_border = intro.picture()
                    self.assertIn(intro_text, text_row(intro_screen, intro_row, font))
                    played = rvm.run_kernel(trial, keys=keys, frames=frames,
                                            system=SYSTEM)
                    self.assertEqual(played.why, 'frames', played.summary())
                    self.assertIsNotNone(played.fg.started)
                    self.assertIsNone(played.fg.ended)
                    self.assertTrue(played.session.owns_screen(played.fg.pid))
                    screen, border = played.picture()
                    self.assertIn(final_text, text_row(screen, final_row, font))
                    self.assertNotEqual(hashlib.sha256(intro_screen).digest(),
                                        hashlib.sha256(screen).digest())
                    if os.environ.get('RBC_TWO_INPUT_CAPTURE_DIR'):
                        dest = Path(os.environ['RBC_TWO_INPUT_CAPTURE_DIR'])
                        dest.mkdir(parents=True, exist_ok=True)
                        rvm.write_png(intro_screen, str(dest / (game + '-blocked.png')),
                                      intro_border)
                        rvm.write_png(screen, str(dest / (game + '-' + name + '.png')),
                                      border)
                    self.assertEqual(tuple(p.read_bytes() for p in (bas, tzx, published)),
                                     originals)


if __name__ == '__main__':
    unittest.main()
