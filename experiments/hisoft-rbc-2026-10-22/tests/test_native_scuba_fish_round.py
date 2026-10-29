"""Original Scuba: real fish catch, counted air-loss, and STOP.

Playback uses only genuine ZX-UX keyboard events. The recorded route
was selected by observing the game's actual swimmer and fish glyphs.
No BASIC, SSX, ROM, RAM, random seed, screen or loader bytes are changed.
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
import zxux
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/14-scuba'
BAS = GAME / 'BASIC/14-scuba.bas'
TZX = GAME / 'BASIC/14-scuba.tzx'
SSX = GAME / 'bin/14-scuba.ssx'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, ROM, SYSTEM, FROZEN))

# Observed native keyboard route: original X (dive), S/F (swim).
# A hold is in genuine keyboard interrupts; every step also advances
# six emulated frames. No synthetic fish collision is possible here.
CATCH_ROUTE = (
    [('F', 12), ('F', 10)] + [(None, 12)] * 6 + [('F', 30)] +
    [(None, 12)] * 16 + [('S', 32)] * 3 +
    [('F', 32), ('S', 21), ('S', 15), ('S', 10), ('F', 18)]
)
assert len(CATCH_ROUTE) == 33


def screenshot(run, font):
    img, border = run.picture()
    line = [''] * 24
    for n in (0, 1, 2, 3, 21):
        line[n] = text_row(img, n, font).strip()
    return img, border, line


def advance_until(run, font, predicate, frames):
    for i in range(frames):
        run.frame()
        if i % 8 == 0:
            snap = screenshot(run, font)
            if predicate(snap[2]):
                return snap
    raise AssertionError(f'expected original Scuba display absent in {frames} frames')


@unittest.skipUnless(READY, 'published Scuba and checked ZX-UX tape required')
class ScubaFishRound(unittest.TestCase):
    def setUp(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        self.original = tuple(p.read_bytes() for p in (BAS, TZX, SSX, ROM, FROZEN))
        bas = self.original[0].decode('ascii')
        for text in (' 365 LET P=P+1', ' 805 PRINT P;', ' 810 PRINT "RAN OUT OF AIR..."',
                     ' 850 IF INKEY$="Y" THEN RUN', ' 860 IF INKEY$="N"'):
            self.assertIn(text, bas)
        linked = rld.parse_ssx(self.original[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(len(self.original[2]), 14000)
        self.assertLessEqual(len(linked['image']) + linked['bss'] + linked['stack'], 14000)
        self.font = self.original[3][0x3D00:0x4000]
        self.assertEqual(len(self.font), 768)

    def tearDown(self):
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX, ROM, FROZEN)),
                         self.original)

    def boot_into_game(self):
        run = rvm.run_kernel(SSX, keys='{WAIT 1900}{ENTER}', frames=2400, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        self.assertIn('FISH CAUGHT = 0', screenshot(run, self.font)[2][0])
        return run

    def test_fish_score_air_loss_then_n_stops(self):
        run = self.boot_into_game()
        run.session.kb.add([('press', zxux.char_keys('X'), 130),
                            ('press', zxux.char_keys('S'), 40)])
        for _ in range(215):
            run.frame()
        for key, hold in CATCH_ROUTE:
            if key:
                run.session.kb.add([('press', zxux.char_keys(key), hold)])
            for _ in range(hold + 6):
                run.frame()
        caught, caught_border, result = screenshot(run, self.font)
        self.assertRegex(result[0], r'FISH CAUGHT\s*=\s*1\b')
        self.assertIn('AIR LEFT', result[1])
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))

        lost, lost_border, end = advance_until(
            run, self.font, lambda ls: 'ANOTHER GO???' in ls[3], 3000)
        self.assertEqual(end[1], '1 FISH BROUGHT BACK FOR SUPPER')
        self.assertEqual(end[2], 'RAN OUT OF AIR...')
        self.assertNotEqual(hashlib.sha256(caught).digest(), hashlib.sha256(lost).digest())
        for _ in range(70):
            run.frame()
        run.session.kb.add([('press', zxux.char_keys('N'), 30)])
        for _ in range(450):
            run.frame()
            if run.fg.ended is not None:
                break
        self.assertIsNotNone(run.fg.ended, 'N did not execute original STOP')
        self.assertEqual(run.fg.status, 0)
        self.assertFalse(run.session.owns_screen(run.fg.pid))

        if os.environ.get('RBC_SCUBA_FISH_CAPTURE_DIR'):
            out = Path(os.environ['RBC_SCUBA_FISH_CAPTURE_DIR'])
            out.mkdir(parents=True, exist_ok=True)
            rvm.write_png(caught, str(out / 'scuba-fish-caught.png'), caught_border)
            rvm.write_png(lost, str(out / 'scuba-fish-air-loss.png'), lost_border)



if __name__ == '__main__':
    unittest.main()
