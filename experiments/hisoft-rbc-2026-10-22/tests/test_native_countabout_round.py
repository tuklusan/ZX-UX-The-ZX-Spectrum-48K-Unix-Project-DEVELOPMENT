"""Original Countabout: reject a wrong answer, accept five flowers, restart.

The unchanged published SSX runs in the real ZX-UX Z80 loader. Framebuffer
words are decoded from the original 768-byte font, not made-up text output.
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

GAME = ROOT / 'src/bonus/60-programs/60-countabout'
BAS = GAME / 'BASIC/60-countabout.bas'
TZX = GAME / 'BASIC/60-countabout.tzx'
SSX = GAME / 'bin/60-countabout.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN))
OPENING = '{WAIT 500}a{WAIT 400}b'


@unittest.skipUnless(READY, 'original game, font and ZX-UX tape required')
class CountaboutFullAnswer(unittest.TestCase):
    def test_wrong_answer_then_correct_answer_and_next_question(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        source_before = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        linked = rld.parse_ssx(source_before[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(source_before[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        run = rvm.run_kernel(SSX, keys=OPENING, frames=2100, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        pic, _ = run.picture()
        self.assertEqual(text_row(pic, 0, font).strip(),
                         'H O W  M A N Y  F L O W E R S ?')

        run.session.kb.type('9')  # The original display has five flowers.
        for _ in range(80):
            run.frame()
        wrong, wrong_border = run.picture()
        self.assertIn('N O,W R O N G  A N S W E R  !',
                      text_row(wrong, 2, font))
        for _ in range(320):
            run.frame()
        again, _ = run.picture()
        self.assertEqual(text_row(again, 0, font).strip(),
                         'H O W  M A N Y  F L O W E R S ?')

        run.session.kb.type('5')
        proved_correct = False
        proved_count = False
        correct_capture = None
        for _ in range(180):
            run.frame()
            snap, border = run.picture()
            proved_correct |= 'C O R R E C T' in text_row(snap, 2, font)
            proved_count |= '5   F L O W E R S' in text_row(snap, 3, font)
            if proved_correct and proved_count and correct_capture is None:
                correct_capture = (snap, border)
        self.assertTrue(proved_correct, 'correct answer never reached original line 360')
        self.assertTrue(proved_count, 'five-flower answer was not printed')
        for _ in range(120):
            run.frame()
        next_round, next_border = run.picture()
        self.assertEqual(text_row(next_round, 0, font).strip(),
                         'PLEASE PRESS ANY KEY')
        self.assertNotEqual(hashlib.sha256(wrong).digest(),
                            hashlib.sha256(next_round).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_COUNTABOUT_CAPTURE_DIR'):
            directory = Path(os.environ['RBC_COUNTABOUT_CAPTURE_DIR'])
            directory.mkdir(parents=True, exist_ok=True)
            for name, (frame, border) in (
                ('countabout-wrong.png', (wrong, wrong_border)),
                ('countabout-correct.png', correct_capture),
                ('countabout-next.png', (next_round, next_border)),
            ):
                rvm.write_png(frame, str(directory / name), border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)),
                         source_before)


if __name__ == '__main__':
    unittest.main()
