"""Original Flying Bomb: full unarmed losing flight and automatic next attempt.

The published SSX and 48K kernel are unchanged. No victory, weapon hit or
full-game completion is inferred from this deterministic losing flight.
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

GAME = ROOT / 'src/bonus/60-programs/12-flying-bomb'
BAS = GAME / 'BASIC/12-flying-bomb.bas'
TZX = GAME / 'BASIC/12-flying-bomb.tzx'
SSX = GAME / 'bin/12-flying-bomb.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(x.is_file() for x in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Flying Bomb and ZX-UX kernel required')
class NativeFlyingBombLossRestart(unittest.TestCase):
    def test_unarmed_target_miss_and_automatic_new_flight(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(x.read_bytes() for x in (BAS, TZX, SSX))
        ssx = rld.parse_ssx(originals[2])
        self.assertEqual(ssx['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(ssx['image']) +
                                 ssx['bss'] + ssx['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys='', frames=350, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        pic, _ = run.picture()
        self.assertIn('FLYING BOMB', text_row(pic, 0, font))
        self.assertIn('SCORE:0', text_row(pic, 2, font))

        for frame in range(1800):
            run.frame()
            if frame % 10 == 0:
                pic, _ = run.picture()
                if 'LOST!' in text_row(pic, 16, font):
                    break
        else:
            self.fail('original BASIC line 810 loss did not occur')
        lost, lost_border = run.picture()
        lost_distance = text_row(lost, 0, font)
        self.assertRegex(lost_distance, r'MLS TO TARGET:-[0-9]')
        self.assertIn('LOST!', text_row(lost, 16, font))
        self.assertIn('SCORE:0', text_row(lost, 2, font))
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))

        # Original BASIC lines 900-920 restart automatically after the miss.
        for _ in range(400):
            run.frame()
        restarted, restarted_border = run.picture()
        distance = text_row(restarted, 0, font)
        self.assertRegex(distance, r'MLS TO TARGET:[ ]*[0-9]')
        self.assertNotIn('LOST!', text_row(restarted, 16, font))
        self.assertIn('SCORE:0', text_row(restarted, 2, font))
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(restarted).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_FLYING_BOMB_CAPTURE_DIR'):
            dest = Path(os.environ['RBC_FLYING_BOMB_CAPTURE_DIR'])
            dest.mkdir(parents=True, exist_ok=True)
            rvm.write_png(lost, str(dest / 'flying-bomb-lost.png'), lost_border)
            rvm.write_png(restarted, str(dest / 'flying-bomb-new-flight.png'),
                          restarted_border)
        self.assertEqual(tuple(x.read_bytes() for x in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
