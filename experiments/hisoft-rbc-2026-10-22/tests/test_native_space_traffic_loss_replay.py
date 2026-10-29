"""Original Space Traffic: native zero-score loss and keyboard restart.

Only original public BAS, TZX and SSX inputs are executed. No RAM, process,
randomness, game executable, renderer or framebuffer is patched. Other
strategies, satellite recovery, shell return and victories remain unverified.
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

GAME = ROOT / 'src/bonus/60-programs/30-space-traffic'
BAS = GAME / 'BASIC/30-space-traffic.bas'
TZX = GAME / 'BASIC/30-space-traffic.tzx'
SSX = GAME / 'bin/30-space-traffic.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN, ROM))


@unittest.skipUnless(READY, 'checked 48K runtime and published game required')
class NativeSpaceTrafficLossReplay(unittest.TestCase):
    def test_five_lives_zero_score_game_over_and_keyboard_replay(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(path.read_bytes() for path in (BAS, TZX, SSX, ROM))
        self.assertIn(b'4135 IF li<>0 THEN RETURN', originals[0])
        self.assertIn(b'4160 PRINT INVERSE 1', originals[0])
        self.assertIn(b'4170 PAUSE 0: CLS : GO SUB 9500: GO TO 70', originals[0])
        image = originals[2]
        layout = rld.parse_ssx(image)
        self.assertEqual(layout['entry'], 0)
        self.assertLessEqual(max(len(image), len(layout['image']) +
                                 layout['bss'] + layout['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)

        run = rvm.run_kernel(SSX,
                             keys='{WAIT 250}{ENTER}{WAIT 100}{ENTER}',
                             frames=1600, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        lost, lost_border = run.picture()
        self.assertEqual(len(lost), 6912)
        self.assertEqual(text_row(lost, 5, font).strip(),
                         'You scored 0 points.')
        self.assertEqual(text_row(lost, 8, font).strip(),
                         'The high-score is 0.')
        self.assertEqual(text_row(lost, 11, font).strip(),
                         'PRESS ANY KEY TO PLAY AGAIN.')

        run.session.kb.type('a')
        for _ in range(350):
            run.frame()
        replayed, replay_border = run.picture()
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(replayed).digest())
        self.assertNotIn('PRESS ANY KEY TO PLAY AGAIN.',
                         '\n'.join(text_row(replayed, y, font)
                                   for y in range(24)))
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        for _ in range(120):
            run.frame()
        following, _ = run.picture()
        self.assertNotEqual(hashlib.sha256(replayed).digest(),
                            hashlib.sha256(following).digest(),
                            'restarted play did not advance after keyboard replay')
        self.assertIsNone(run.fg.ended)
        if os.environ.get('RBC_SPACE_TRAFFIC_CAPTURE_DIR'):
            out = Path(os.environ['RBC_SPACE_TRAFFIC_CAPTURE_DIR'])
            out.mkdir(parents=True, exist_ok=True)
            rvm.write_png(lost, str(out / 'space-traffic-gameover.png'),
                          lost_border)
            rvm.write_png(replayed, str(out / 'space-traffic-replayed.png'),
                          replay_border)
        self.assertEqual(tuple(path.read_bytes() for path in
                               (BAS, TZX, SSX, ROM)), originals)


if __name__ == '__main__':
    unittest.main()
