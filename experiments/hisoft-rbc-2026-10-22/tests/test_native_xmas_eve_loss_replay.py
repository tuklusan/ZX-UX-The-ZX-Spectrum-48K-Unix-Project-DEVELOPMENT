"""Original Xmas Eve: unprotected houses cause game over; a key restarts.

One losing round and replay in the unchanged ZX-UX 48K native game.
Not a successful gift delivery, every control, or full playthrough proof.
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

GAME = ROOT / 'src/bonus/60-programs/37-xmas-eve'
BAS = GAME / 'BASIC/37-xmas-eve.bas'
TZX = GAME / 'BASIC/37-xmas-eve.tzx'
SSX = GAME / 'bin/37-xmas-eve.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(x.is_file() for x in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Xmas Eve, font and ZX-UX required')
class NativeXmasEveLossReplay(unittest.TestCase):
    def test_no_presents_game_over_and_keyboard_replay(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(x.read_bytes() for x in (BAS, TZX, SSX))
        linked = rld.parse_ssx(originals[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys='', frames=400, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        intro, _ = run.picture()
        self.assertIn('PRESS ANY KEY TO SEE MORE.', text_row(intro, 20, font))
        run.session.kb.type('a')
        for _ in range(150):
            run.frame()
        instructions, _ = run.picture()
        self.assertIn('PRESS ANY KEY TO START', text_row(instructions, 20, font))
        run.session.kb.type('b')
        for _ in range(150):
            run.frame()
        started, _ = run.picture()
        self.assertIn('PRESENTS:0', text_row(started, 0, font))

        for frame in range(3500):
            run.frame()
            if frame % 20 == 0:
                image, _ = run.picture()
                if 'PRESS ANY KEY TO PLAY AGAIN' in text_row(image, 11, font):
                    break
        else:
            self.fail('original BASIC line 6050 replay prompt never reached')
        lost, lost_border = run.picture()
        self.assertIn('G A M E  O V E R', text_row(lost, 8, font))
        self.assertIn('PRESS ANY KEY TO PLAY AGAIN', text_row(lost, 11, font))
        self.assertIn('PRESENTS:0', text_row(lost, 0, font))
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))

        run.session.kb.type('c')
        for _ in range(250):
            run.frame()
        replay, replay_border = run.picture()
        self.assertIn('PRESENTS:', text_row(replay, 0, font))
        self.assertNotIn('G A M E  O V E R', text_row(replay, 8, font))
        self.assertNotIn('PRESS ANY KEY TO PLAY AGAIN', text_row(replay, 11, font))
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(replay).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_XMAS_EVE_CAPTURE_DIR'):
            dest = Path(os.environ['RBC_XMAS_EVE_CAPTURE_DIR'])
            dest.mkdir(parents=True, exist_ok=True)
            rvm.write_png(lost, str(dest / 'xmas-eve-gameover.png'), lost_border)
            rvm.write_png(replay, str(dest / 'xmas-eve-restarted.png'), replay_border)
        self.assertEqual(tuple(x.read_bytes() for x in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
