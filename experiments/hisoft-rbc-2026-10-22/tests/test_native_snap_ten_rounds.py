"""Published Snap: finish ten timed pictures without a key in real ZX-UX.

The timed-out losing result is proven, but INPUT replay is not.
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

GAME = ROOT / 'src/bonus/60-programs/16-snap'
BAS = GAME / 'BASIC/16-snap.bas'
TZX = GAME / 'BASIC/16-snap.tzx'
SSX = GAME / 'bin/16-snap.ssx'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
READY = all(p.is_file() for p in (BAS, TZX, SSX, SYSTEM, FROZEN, FONT))


@unittest.skipUnless(READY, 'checked original game, ZX-UX and font required')
class NativeSnapTenRoundResult(unittest.TestCase):
    def test_ten_picture_timeouts_reach_original_score_summary(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        self.assertIn(b'IF P=10 THEN GO TO 400', originals[0])
        self.assertIn(b'YOU HAVE ', originals[0])
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        self.assertEqual(hashlib.sha256(font).hexdigest(),
                         '7b8faa46ee8359ea1cf141a85f618f9f3716334495f3c5c107bb1e5cb86cc468')
        parsed = rld.parse_ssx(originals[2])
        self.assertEqual(parsed['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(parsed['image']) +
                                 parsed['bss'] + parsed['stack']), 14000)
        run = rvm.run_kernel(SSX, keys='', frames=2200, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        picture, border = run.picture()
        self.assertEqual(len(picture), 6912)
        self.assertIn('CORRECT OUT OF:10', text_row(picture, 1, font))
        self.assertIn('YOU HAVE 0 CORRECT OUT OF 10 IN', text_row(picture, 10, font))
        self.assertIn('BEST TIME SO FAR', text_row(picture, 11, font))
        self.assertIn('PRESS<ENTER>FOR NEXT GAME', text_row(picture, 23, font))
        if os.environ.get('RBC_SNAP_ROUND_CAPTURE_DIR'):
            out = Path(os.environ['RBC_SNAP_ROUND_CAPTURE_DIR'])
            out.mkdir(parents=True, exist_ok=True)
            rvm.write_png(picture, str(out / 'snap-ten-round-score.png'), border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
