"""Run an original 100-shot Flying Geese round in the real ZX-UX loader.

This verifies game-over and score, not a successful INPUT-driven replay.
The published SSX, BAS and TZX are unmodified; the emulator presses real keys.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).resolve().parent)]
import rld
import rvm
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/39-flying-geese'
BAS = GAME / 'BASIC/39-flying-geese.bas'
TZX = GAME / 'BASIC/39-flying-geese.tzx'
SSX = GAME / 'bin/39-flying-geese.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN))
SHOTS = '{WAIT 100}' + 'a' * 130


@unittest.skipUnless(READY, 'original game, font and ZX-UX tape required')
class NativeFlyingGeeseRound(unittest.TestCase):
    def test_real_100_shot_game_over_and_score(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        original = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        linked = rld.parse_ssx(original[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(original[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys=SHOTS, frames=4500, system=SYSTEM)
        self.assertIn(run.why, ('input', 'frames'), run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertFalse(run.session.kb.busy())
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        image, border = run.picture()
        self.assertEqual(len(image), 6912)
        # The 100-shot scoreboard is authoritative; the rendered SHOTS
        # counter can be one frame ahead at the capture boundary.
        first_row = text_row(image, 0, font).strip()
        self.assertRegex(first_row, r'^SHOTS:10[12] <A> TO FIRE   SCORE 5$')
        self.assertEqual(text_row(image, 9, font).strip(), 'GAME OVER')
        self.assertEqual(text_row(image, 11, font).strip(),
                         'SCORE:5 IN 100 SHOTS')
        self.assertTrue(text_row(image, 13, font).startswith('    HIGHEST SCORE:5'),
                        'scoreboard high score missing')
        if os.environ.get('RBC_GEESE_CAPTURE_DIR'):
            out = Path(os.environ['RBC_GEESE_CAPTURE_DIR'])
            out.mkdir(parents=True, exist_ok=True)
            rvm.write_png(image, str(out / 'flying-geese-game-over.png'), border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)),
                         original)


if __name__ == '__main__':
    unittest.main()
