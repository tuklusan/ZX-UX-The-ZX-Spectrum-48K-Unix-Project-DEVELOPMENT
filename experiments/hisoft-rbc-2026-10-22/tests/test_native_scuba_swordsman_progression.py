"""Two original published SSX games, real keyboard screen progression.

Scuba: start after the authentic slow ROM-font copy countdown. Swordsman:
wait for a natural defeat, then use the original Y replay input. Neither test
rewrites BASIC, TZX, SSX, kernel, or ROM; a changed framebuffer alone is not
claimed to prove every gameplay branch.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).resolve().parent)]
import rld
import rvm
from test_native_oxo_complete_round import text_row

GAMES = ROOT / 'src/bonus/60-programs'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (FONT, ROM, SYSTEM, FROZEN))
CASES = (
    ('14-scuba', '', '{WAIT 1900}{ENTER}{WAIT 100}X', 2400,
     'GOOD LUCK...ENTER TO START', 21, 'FISH CAUGHT = 0', 0, 'scuba'),
    ('54-swordsman', '', '{WAIT 550}Y', 620,
     'ANOTHER HERO BITES THE DUST.', 7, 'TOTAL POINTS=1', 0, 'swordsman'),
)


def checked_run(source: Path, keys: str, frames: int):
    run = rvm.run_kernel(source, keys=keys, frames=frames, system=SYSTEM)
    if run.fg.started is None or run.why != 'frames' or run.fg.ended is not None:
        raise AssertionError('published ZX-UX process not running at checked frame')
    if not run.session.owns_screen(run.fg.pid):
        raise AssertionError('original game did not own the screen')
    image, border = run.picture()
    if len(image) != 6912:
        raise AssertionError('48K framebuffer not available')
    return image, border


@unittest.skipUnless(READY, 'original ZX-UX, checked ROM and native font required')
class NativeScubaSwordsmanProgression(unittest.TestCase):
    def test_original_scuba_enter_and_swordsman_replay(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        sword_font = FONT.read_bytes()
        scuba_font = ROM.read_bytes()[0x3d00:0x4000]
        self.assertEqual(len(sword_font), len(scuba_font))
        self.assertEqual(len(sword_font), 768)
        for game, quiet_keys, played_keys, frames, quiet_text, quiet_row, played_text, played_row, capture in CASES:
            with self.subTest(game=game):
                folder = GAMES / game
                bas = folder / 'BASIC' / (game + '.bas')
                tzx = folder / 'BASIC' / (game + '.tzx')
                ssx = folder / 'bin' / (game + '.ssx')
                originals = tuple(p.read_bytes() for p in (bas, tzx, ssx))
                parsed = rld.parse_ssx(originals[2])
                self.assertEqual(parsed['entry'], 0)
                self.assertLessEqual(max(len(originals[2]), len(parsed['image']) +
                                         parsed['bss'] + parsed['stack']), 14000)
                quiet, quiet_border = checked_run(ssx, quiet_keys, frames)
                played, played_border = checked_run(ssx, played_keys, frames)
                font = scuba_font if game == '14-scuba' else sword_font
                self.assertIn(quiet_text, text_row(quiet, quiet_row, font))
                self.assertIn(played_text, text_row(played, played_row, font))
                self.assertNotEqual(hashlib.sha256(quiet).digest(),
                                    hashlib.sha256(played).digest())
                if os.environ.get('RBC_TWO_INKEY_CAPTURE_DIR'):
                    dest = Path(os.environ['RBC_TWO_INKEY_CAPTURE_DIR'])
                    dest.mkdir(parents=True, exist_ok=True)
                    rvm.write_png(quiet, str(dest / (capture + '-waiting.png')),
                                  quiet_border)
                    rvm.write_png(played, str(dest / (capture + '-progressed.png')),
                                  played_border)
                self.assertEqual(tuple(p.read_bytes() for p in (bas, tzx, ssx)),
                                 originals)


if __name__ == '__main__':
    unittest.main()
