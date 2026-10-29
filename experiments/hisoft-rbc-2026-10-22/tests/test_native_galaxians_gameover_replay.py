"""Original Galaxians: observe a complete native loss and restart.

No ROM or published program is edited. This checks a losing round only;
it does not claim a victory, every level, or complete weapon behavior.
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

GAME = ROOT / 'src/bonus/60-programs/25-galaxians'
BAS = GAME / 'BASIC/25-galaxians.bas'
TZX = GAME / 'BASIC/25-galaxians.tzx'
SSX = GAME / 'bin/25-galaxians.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Galaxians, recovered font and ZX-UX required')
class NativeGalaxiansGameoverReplay(unittest.TestCase):
    def test_gameover_prompt_and_new_fleet(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        original = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        linked = rld.parse_ssx(original[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(original[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys='', frames=500, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        intro, _ = run.picture()
        self.assertIn('PRESS ANY KEY TO START', text_row(intro, 20, font))

        run.session.kb.type('a')
        for frame in range(2000):
            run.frame()
            if frame % 25 == 0:
                picture, _ = run.picture()
                if 'G A M E  O V E R' in text_row(picture, 10, font):
                    break
        else:
            self.fail('original BASIC line 4050 game-over was never reached')
        # The line 4050 prompt follows the game-over label on the screen.
        for _ in range(100):
            run.frame()
        gameover, border = run.picture()
        self.assertEqual(text_row(gameover, 10, font).strip(), 'G A M E  O V E R')
        self.assertEqual(text_row(gameover, 18, font).strip(),
                         'PRESS ANY KEY TO PLAY AGAIN')
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        self.assertIsNone(run.fg.ended)
        run.session.kb.type('a')
        for _ in range(350):
            run.frame()
        replay, replay_border = run.picture()
        self.assertIn('HIGH-SCORE:', text_row(replay, 0, font))
        self.assertNotIn('G A M E  O V E R', text_row(replay, 10, font))
        self.assertNotIn('PRESS ANY KEY TO PLAY AGAIN', text_row(replay, 18, font))
        self.assertNotEqual(hashlib.sha256(gameover).digest(),
                            hashlib.sha256(replay).digest())
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        self.assertIsNone(run.fg.ended)
        if os.environ.get('RBC_GALAXIANS_CAPTURE_DIR'):
            out = Path(os.environ['RBC_GALAXIANS_CAPTURE_DIR'])
            out.mkdir(parents=True, exist_ok=True)
            rvm.write_png(gameover, str(out / 'galaxians-gameover.png'), border)
            rvm.write_png(replay, str(out / 'galaxians-restarted.png'), replay_border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), original)


if __name__ == '__main__':
    unittest.main()
