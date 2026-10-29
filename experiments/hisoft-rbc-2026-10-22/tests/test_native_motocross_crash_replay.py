"""Original Motocross: obstacle crash, menu retry, and a second crash.

Use the unchanged ZX-UX native game and actual keyboard. One losing run
and menu restart are proved, not successful racing, stunt-cycle or STOP.
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

GAME = ROOT / 'src/bonus/60-programs/06-motocross'
BAS = GAME / 'BASIC/06-motocross.bas'
TZX = GAME / 'BASIC/06-motocross.tzx'
SSX = GAME / 'bin/06-motocross.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(x.is_file() for x in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Motocross, font and ZX-UX required')
class NativeMotocrossCrashReplay(unittest.TestCase):
    def test_first_obstacle_crash_then_retry_then_second_crash(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(x.read_bytes() for x in (BAS, TZX, SSX))
        linked = rld.parse_ssx(originals[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys='', frames=600, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        intro, _ = run.picture()
        self.assertIn('MOTOCROSS', text_row(intro, 0, font))
        self.assertIn('This Program Consists Of Two', text_row(intro, 2, font))
        run.session.kb.type('1')
        for frame in range(500):
            run.frame()
            if frame % 10 == 0:
                screen, _ = run.picture()
                if 'Bad Luck! You crashed.' in text_row(screen, 0, font):
                    break
        else:
            self.fail('original BASIC line 1030 obstacle crash not reached')
        crashed, crash_border = run.picture()
        self.assertIn('Press the key which corresponds', text_row(crashed, 2, font))
        self.assertIn('1...Moto-cross', text_row(crashed, 5, font))
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        run.session.kb.type('1')
        for _ in range(75):
            run.frame()
        riding, riding_border = run.picture()
        self.assertNotIn('Bad Luck! You crashed.', text_row(riding, 0, font))
        self.assertNotIn('1...Moto-cross', text_row(riding, 5, font))
        self.assertNotEqual(hashlib.sha256(crashed).digest(),
                            hashlib.sha256(riding).digest())
        for frame in range(350):
            run.frame()
            if frame % 10 == 0:
                screen, _ = run.picture()
                if 'Bad Luck! You crashed.' in text_row(screen, 0, font):
                    break
        else:
            self.fail('second original obstacle crash not reached')
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_MOTOCROSS_CAPTURE_DIR'):
            output = Path(os.environ['RBC_MOTOCROSS_CAPTURE_DIR'])
            output.mkdir(parents=True, exist_ok=True)
            rvm.write_png(crashed, str(output / 'motocross-crashed.png'),
                          crash_border)
            rvm.write_png(riding, str(output / 'motocross-restarted.png'),
                          riding_border)
        self.assertEqual(tuple(x.read_bytes() for x in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
