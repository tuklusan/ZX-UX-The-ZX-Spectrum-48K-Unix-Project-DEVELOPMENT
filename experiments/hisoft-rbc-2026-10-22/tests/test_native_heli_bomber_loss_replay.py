"""Original Heli-Bomber: genuine native loss, score and restart.

The ZX-UX loader, original SSX, BASIC inputs, and kernel are unchanged.
This proves one losing round and restart, not a victory or every control path.
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

GAME = ROOT / 'src/bonus/60-programs/33-heli-bomber'
BAS = GAME / 'BASIC/33-heli-bomber.bas'
TZX = GAME / 'BASIC/33-heli-bomber.tzx'
SSX = GAME / 'bin/33-heli-bomber.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Heli-Bomber, font and ZX-UX required')
class NativeHeliBomberLossReplay(unittest.TestCase):
    def test_unanswered_bombs_end_round_and_key_restarts_city(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
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
        self.assertIn('Press any key to start', text_row(intro, 20, font))
        run.session.kb.type('a')
        for frame in range(1200):
            run.frame()
            if frame % 25 == 0:
                screen, _ = run.picture()
                if 'Press any key to restart' in text_row(screen, 16, font):
                    break
        else:
            self.fail('original BASIC line 3010 restart prompt not reached')
        lost, loss_border = run.picture()
        self.assertEqual(text_row(lost, 10, font).strip(), 'END OF GAME')
        self.assertIn('Your score was 0', text_row(lost, 12, font))
        self.assertIn('High score 0', text_row(lost, 14, font))
        self.assertEqual(text_row(lost, 16, font).strip(),
                         'Press any key to restart')
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        self.assertIsNone(run.fg.ended)
        run.session.kb.type('b')
        for _ in range(150):
            run.frame()
        replay, replay_border = run.picture()
        self.assertNotIn('END OF GAME', text_row(replay, 10, font))
        self.assertNotIn('Press any key to restart', text_row(replay, 16, font))
        self.assertIn('+', text_row(replay, 10, font))
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(replay).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_HELI_BOMBER_CAPTURE_DIR'):
            output = Path(os.environ['RBC_HELI_BOMBER_CAPTURE_DIR'])
            output.mkdir(parents=True, exist_ok=True)
            rvm.write_png(lost, str(output / 'heli-bomber-gameover.png'), loss_border)
            rvm.write_png(replay, str(output / 'heli-bomber-restarted.png'), replay_border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
