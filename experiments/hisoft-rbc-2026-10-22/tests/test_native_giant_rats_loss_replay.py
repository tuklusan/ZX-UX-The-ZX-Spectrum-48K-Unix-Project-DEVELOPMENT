"""Original Giant Rats: five lost lives, score display, and actual replay.

Published SSX, original inputs, ROM and ZX-UX release tape stay untouched.
This proves a losing run and replay, not a winning route or every move.
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

GAME = ROOT / 'src/bonus/60-programs/35-giant-rats'
BAS = GAME / 'BASIC/35-giant-rats.bas'
TZX = GAME / 'BASIC/35-giant-rats.tzx'
SSX = GAME / 'bin/35-giant-rats.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Giant Rats, font and ZX-UX required')
class NativeGiantRatsLossReplay(unittest.TestCase):
    def test_unanswered_timer_consumes_lives_and_replay_resets_arena(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        decoded = rld.parse_ssx(originals[2])
        self.assertEqual(decoded['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(decoded['image']) +
                                 decoded['bss'] + decoded['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys='', frames=350, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        intro, _ = run.picture()
        self.assertIn('Press any key...', text_row(intro, 21, font))
        run.session.kb.type('a')
        for _ in range(140):
            run.frame()
        help_screen, _ = run.picture()
        self.assertIn('PRESS ANY KEY TO START.', text_row(help_screen, 13, font))
        run.session.kb.type('b')
        for frame in range(3000):
            run.frame()
            if frame % 20 == 0:
                pic, _ = run.picture()
                if 'PRESS ANY KEY TO PLAY AGAIN' in text_row(pic, 8, font):
                    break
        else:
            self.fail('five-life original game-over prompt never appeared')
        lost, lost_border = run.picture()
        self.assertEqual(text_row(lost, 2, font).strip(), 'You scored 0 points.')
        self.assertEqual(text_row(lost, 5, font).strip(), 'The high-score is 0')
        self.assertEqual(text_row(lost, 8, font).strip(),
                         'PRESS ANY KEY TO PLAY AGAIN')
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        run.session.kb.type('c')
        for _ in range(150):
            run.frame()
        restarted, restart_border = run.picture()
        self.assertNotIn('PRESS ANY KEY TO PLAY AGAIN',
                         text_row(restarted, 8, font))
        self.assertNotIn('You scored 0 points.', text_row(restarted, 2, font))
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(restarted).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_GIANT_RATS_CAPTURE_DIR'):
            path = Path(os.environ['RBC_GIANT_RATS_CAPTURE_DIR'])
            path.mkdir(parents=True, exist_ok=True)
            rvm.write_png(lost, str(path / 'giant-rats-gameover.png'), lost_border)
            rvm.write_png(restarted, str(path / 'giant-rats-restarted.png'),
                          restart_border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
