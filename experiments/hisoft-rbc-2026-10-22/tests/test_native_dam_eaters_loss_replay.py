"""Original Dam Eaters: an unprotected dam falls and keyboard restarts play.

Checks one losing round and replay in the unchanged ZX-UX 48K loader.
It does not claim winning, every cannon, or complete gameplay coverage.
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

GAME = ROOT / 'src/bonus/60-programs/31-dam-eaters'
BAS = GAME / 'BASIC/31-dam-eaters.bas'
TZX = GAME / 'BASIC/31-dam-eaters.tzx'
SSX = GAME / 'bin/31-dam-eaters.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(x.is_file() for x in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN,
                                  SYSTEM.with_name('kernel.json')))


@unittest.skipUnless(READY, 'original Dam Eaters and ZX-UX runtime required')
class NativeDamEatersLossReplay(unittest.TestCase):
    def test_first_dam_breach_score_and_replay(self):
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
        opening, _ = run.picture()
        self.assertIn('Press any key to start', text_row(opening, 14, font) +
                      text_row(opening, 15, font) + text_row(opening, 16, font))
        run.session.kb.type('a')
        for frame in range(1600):
            run.frame()
            if frame % 20 == 0:
                display, _ = run.picture()
                if 'PRESS A KEY TO PLAY AGAIN' in text_row(display, 11, font):
                    break
        else:
            self.fail('original BASIC line 4080 loss prompt never appeared')
        lost, loss_border = run.picture()
        self.assertIn('You Scored 0 Points.', text_row(lost, 4, font))
        self.assertIn('The High-Score Is 0', text_row(lost, 9, font))
        self.assertIn('PRESS A KEY TO PLAY AGAIN', text_row(lost, 11, font))
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        run.session.kb.type('b')
        for _ in range(200):
            run.frame()
        replay, replay_border = run.picture()
        self.assertIn('Score:0', text_row(replay, 0, font))
        self.assertNotIn('You Scored', text_row(replay, 4, font))
        self.assertNotIn('PRESS A KEY TO PLAY AGAIN', text_row(replay, 11, font))
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(replay).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_DAM_EATERS_CAPTURE_DIR'):
            output = Path(os.environ['RBC_DAM_EATERS_CAPTURE_DIR'])
            output.mkdir(parents=True, exist_ok=True)
            rvm.write_png(lost, str(output / 'dam-eaters-breached.png'), loss_border)
            rvm.write_png(replay, str(output / 'dam-eaters-restarted.png'),
                          replay_border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
