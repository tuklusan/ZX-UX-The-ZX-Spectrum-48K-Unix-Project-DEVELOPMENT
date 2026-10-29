"""Original published Bricklayer: build the wall to a natural game-over.

The test runs the ZX-UX Z80 kernel and sends one real key to leave the
instructions. It never changes BASIC, linked SSX, RAM, or framebuffer.
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
import zxux
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/42-bricklayer'
BAS = GAME / 'BASIC/42-bricklayer.bas'
TZX = GAME / 'BASIC/42-bricklayer.tzx'
SSX = GAME / 'bin/42-bricklayer.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN))


@unittest.skipUnless(READY, 'checked ZX-UX, font, and original game required')
class BricklayerNaturalGameover(unittest.TestCase):
    def test_wall_reaches_gameover_without_losing_a_life(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        original = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        listing = original[0].decode('ascii')
        self.assertIn(' 125 IF b=3 THEN GO TO 1000', listing)
        self.assertIn('1030 PRINT FLASH 1;AT 15,7;"ANOTHER GAME?"', listing)
        linked = rld.parse_ssx(original[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(original[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys='', frames=1800, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        intro, _ = run.picture()
        self.assertIn('Z...........DROPS BOMBS', text_row(intro, 15, font))
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))

        run.session.kb.add([('press', zxux.char_keys('a'), 30)])
        captured = None
        for step in range(4200):
            run.frame()
            if step % 20 == 0:
                screen, border = run.picture()
                message = text_row(screen, 15, font)
                if 'ANOTHER GAME?' in message:
                    captured = screen, border
                    break
        self.assertIsNotNone(captured, 'original game-over not reached')
        ended, border = captured
        score = text_row(ended, 0, font)
        self.assertEqual(score.strip(), 'SCORE:0      HI:0       LIVES:10')
        self.assertNotEqual(hashlib.sha256(intro).digest(), hashlib.sha256(ended).digest())
        self.assertIsNone(run.fg.ended, 'the game should still be at its INPUT prompt')
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_BRICKLAYER_WALL_CAPTURE_DIR'):
            directory = Path(os.environ['RBC_BRICKLAYER_WALL_CAPTURE_DIR'])
            directory.mkdir(parents=True, exist_ok=True)
            rvm.write_png(ended, str(directory / 'bricklayer-wall-gameover.png'), border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), original)


if __name__ == '__main__':
    unittest.main()
