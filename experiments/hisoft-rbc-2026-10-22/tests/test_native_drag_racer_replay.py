"""Original published Drag Racer: engine failure and real-key replay in ZX-UX.

The native SSX and both BASIC originals are read-only test inputs.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'),
                str(Path(__file__).resolve().parent)]
import rld
import rvm
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/49-drag-racer'
BAS = GAME / 'BASIC/49-drag-racer.bas'
TZX = GAME / 'BASIC/49-drag-racer.tzx'
SSX = GAME / 'bin/49-drag-racer.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN))


@unittest.skipUnless(READY, 'verified original game, ROM font and ZX-UX required')
class NativeDragRacerReplay(unittest.TestCase):
    def test_engine_failure_restart_key_resets_screen(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        original = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        linked = rld.parse_ssx(original[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(original[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        over = rvm.run_kernel(SSX, keys='{WAIT 500}x', frames=1700,
                              system=SYSTEM)
        self.assertEqual(over.why, 'frames')
        self.assertIsNotNone(over.fg.started)
        self.assertIsNone(over.fg.ended)
        self.assertTrue(over.session.owns_screen(over.fg.pid))
        screen_over, border_over = over.picture()
        self.assertIn('Engine blown', text_row(screen_over, 0, font))
        self.assertIn('Press any key to restart',
                      text_row(screen_over, 1, font))

        again = rvm.run_kernel(SSX,
                               keys='{WAIT 500}x{WAIT 1300}x',
                               frames=2100, system=SYSTEM)
        self.assertEqual(again.why, 'frames')
        self.assertIsNotNone(again.fg.started)
        self.assertIsNone(again.fg.ended)
        self.assertTrue(again.session.owns_screen(again.fg.pid))
        screen_again, border_again = again.picture()
        self.assertNotEqual(hashlib.sha256(screen_over).digest(),
                            hashlib.sha256(screen_again).digest())
        self.assertNotIn('Engine blown', text_row(screen_again, 0, font))
        self.assertNotIn('Press any key to restart',
                         text_row(screen_again, 1, font))
        self.assertIn('Drag', text_row(screen_again, 10, font))

        if os.environ.get('RBC_DRAG_RACER_CAPTURE_DIR'):
            dest = Path(os.environ['RBC_DRAG_RACER_CAPTURE_DIR'])
            dest.mkdir(parents=True, exist_ok=True)
            rvm.write_png(screen_over, str(dest / 'drag-racer-engine-blown.png'),
                          border_over)
            rvm.write_png(screen_again, str(dest / 'drag-racer-after-restart-key.png'),
                          border_again)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)),
                         original)


if __name__ == '__main__':
    unittest.main()
