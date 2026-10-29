"""Original Buzzy Bee: natural bee collision, survival time, and replay.

Only the published native game is run by the real ZX-UX Z80 emulator.
A losing round and restart do not establish victory or every control key.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).resolve().parent)]
import rld
import rvm
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/32-buzzy-bee'
BAS = GAME / 'BASIC/32-buzzy-bee.bas'
TZX = GAME / 'BASIC/32-buzzy-bee.tzx'
SSX = GAME / 'bin/32-buzzy-bee.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Buzzy Bee, font and ZX-UX required')
class NativeBuzzyBeeLossReplay(unittest.TestCase):
    def test_unmoved_bee_collision_and_next_round(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        decoded = rld.parse_ssx(originals[2])
        self.assertEqual(decoded['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(decoded['image']) +
                                 decoded['bss'] + decoded['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys='', frames=550, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        intro, _ = run.picture()
        self.assertIn('PRESS ANY KEY TO START.', text_row(intro, 21, font))
        run.session.kb.type('a')
        for frame in range(2500):
            run.frame()
            if frame % 25 == 0:
                pic, _ = run.picture()
                if 'Press any key to play again.' in text_row(pic, 11, font):
                    break
        else:
            self.fail('original survival summary and replay prompt never appeared')
        lost, border_lost = run.picture()
        self.assertRegex(text_row(lost, 4, font).strip(),
                         r'^You survived for [0-9]+ seconds\.$')
        self.assertIn('Well done! That', text_row(lost, 7, font))
        self.assertIn('recorded time!', text_row(lost, 8, font))
        self.assertEqual(text_row(lost, 11, font).strip(),
                         'Press any key to play again.')
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        run.session.kb.type('b')
        for _ in range(120):
            run.frame()
        restarted, border_restarted = run.picture()
        self.assertNotIn('Press any key to play again.',
                         text_row(restarted, 11, font))
        self.assertNotIn('You survived for ', text_row(restarted, 4, font))
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(restarted).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_BUZZY_BEE_CAPTURE_DIR'):
            output = Path(os.environ['RBC_BUZZY_BEE_CAPTURE_DIR'])
            output.mkdir(parents=True, exist_ok=True)
            rvm.write_png(lost, str(output / 'buzzy-bee-gameover.png'), border_lost)
            rvm.write_png(restarted, str(output / 'buzzy-bee-restarted.png'),
                          border_restarted)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
