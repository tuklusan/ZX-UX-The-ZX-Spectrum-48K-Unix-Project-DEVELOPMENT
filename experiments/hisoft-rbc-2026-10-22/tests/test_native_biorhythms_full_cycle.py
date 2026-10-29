"""Original Biorhythms: six entered date values, chart and keyboard restart.

Uses the unchanged published ras/rld-linked native SSX in the real 48K ZX-UX
loader. A picture alone does not establish mathematical chart accuracy.
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

GAME = ROOT / 'src/bonus/60-programs/23-biorhythms'
BAS = GAME / 'BASIC/23-biorhythms.bas'
TZX = GAME / 'BASIC/23-biorhythms.tzx'
SSX = GAME / 'bin/23-biorhythms.ssx'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
READY = all(p.is_file() for p in (BAS, TZX, SSX, SYSTEM, FROZEN,
                                  FONT, ROM))
KEYS = ('{WAIT 100}1980{ENTER}{WAIT 30}10{ENTER}{WAIT 30}28{ENTER}'
        '{WAIT 30}2026{ENTER}{WAIT 30}10{ENTER}{WAIT 30}28{ENTER}')


@unittest.skipUnless(READY, 'checked ZX-UX, published game and font required')
class NativeBiorhythmsFullCycle(unittest.TestCase):
    def test_six_date_inputs_chart_then_fresh_entry_screen(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX, ROM))
        self.assertIn(b'Physical cycle', originals[0])
        self.assertIn(b'Emotional cycle', originals[0])
        self.assertIn(b'Intellectual cycle', originals[0])
        self.assertIn(b'Press a key to restart', originals[0])
        linked = rld.parse_ssx(originals[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)

        run = rvm.run_kernel(SSX, keys=KEYS, frames=3400, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        chart, chart_border = run.picture()
        self.assertEqual(len(chart), 6912)
        self.assertIn('Biorhythm for', text_row(chart, 0, font))
        self.assertIn('28/10/2026', text_row(chart, 0, font))
        self.assertIn('Press a key to restart', text_row(chart, 20, font))

        run.session.kb.type('a')
        for _ in range(300):
            run.frame()
        fresh, fresh_border = run.picture()
        self.assertEqual(text_row(fresh, 0, font).strip(), 'BIORHYTHMS')
        for row, label in ((4, 'BIRTH YEAR:'), (6, 'BIRTH MONTH:'),
                           (8, 'BIRTH DAY:'), (11, 'YEAR REQUIRED:'),
                           (13, 'MONTH REQUIRED:'), (15, 'DAY REQUIRED')):
            self.assertIn(label, text_row(fresh, row, font))
        self.assertIn('Enter details now (numeric)',
                      text_row(fresh, 21, font))
        self.assertNotEqual(hashlib.sha256(chart).digest(),
                            hashlib.sha256(fresh).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_BIORHYTHMS_CAPTURE_DIR'):
            out = Path(os.environ['RBC_BIORHYTHMS_CAPTURE_DIR'])
            out.mkdir(parents=True, exist_ok=True)
            rvm.write_png(chart, str(out / 'biorhythms-chart.png'), chart_border)
            rvm.write_png(fresh, str(out / 'biorhythms-restarted.png'), fresh_border)
        self.assertEqual(tuple(p.read_bytes() for p in
                               (BAS, TZX, SSX, ROM)), originals)


if __name__ == '__main__':
    unittest.main()
