"""Original published Swordsman: actual combat followed by natural defeat.

The no-key run verifies game progression, not a player-controlled victory or
response to the final replay prompt. All original input and executable bytes
remain unchanged; the kernel and emulator run the published native SSX.
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

GAME = ROOT / 'src/bonus/60-programs/54-swordsman'
BAS = GAME / 'BASIC/54-swordsman.bas'
TZX = GAME / 'BASIC/54-swordsman.tzx'
SSX = GAME / 'bin/54-swordsman.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN))


@unittest.skipUnless(READY, 'published Swordsman, compiler font and kernel required')
class NativeSwordsmanNaturalLoss(unittest.TestCase):
    def test_combat_progresses_to_original_defeat_and_score(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        linked = rld.parse_ssx(originals[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        pictures = {}
        for name, frames in (('combat', 200), ('defeat', 500)):
            with self.subTest(phase=name):
                run = rvm.run_kernel(SSX, keys='', frames=frames,
                                     system=SYSTEM)
                self.assertEqual(run.why, 'frames', run.summary())
                self.assertIsNotNone(run.fg.started)
                self.assertIsNone(run.fg.ended)
                self.assertTrue(run.session.owns_screen(run.fg.pid))
                picture, border = run.picture()
                self.assertEqual(len(picture), 6912)
                pictures[name] = picture
                if os.environ.get('RBC_SWORDSMAN_CAPTURE_DIR'):
                    dest = Path(os.environ['RBC_SWORDSMAN_CAPTURE_DIR'])
                    dest.mkdir(parents=True, exist_ok=True)
                    rvm.write_png(picture, str(dest / ('swordsman-' + name + '.png')),
                                  border)
        combat, defeat = pictures['combat'], pictures['defeat']
        self.assertIn('TOTAL POINTS=1', text_row(combat, 0, font))
        self.assertIn("IT'S THE GANGRENE GOAT", text_row(combat, 12, font))
        self.assertNotIn('ANOTHER HERO BITES THE DUST', text_row(combat, 7, font))
        self.assertIn('ANOTHER HERO BITES THE DUST', text_row(defeat, 7, font))
        self.assertIn('YOU KILLED 0 MONSTERS', text_row(defeat, 9, font))
        self.assertIn('SCORING 1 POINTS', text_row(defeat, 10, font))
        self.assertIn("PRESS 'Y' TO PLAY AGAIN, 'N' TO",
                      text_row(defeat, 12, font))
        self.assertIn('FINISH', text_row(defeat, 13, font))
        self.assertNotEqual(hashlib.sha256(combat).digest(),
                            hashlib.sha256(defeat).digest())
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)),
                         originals)


if __name__ == '__main__':
    unittest.main()
