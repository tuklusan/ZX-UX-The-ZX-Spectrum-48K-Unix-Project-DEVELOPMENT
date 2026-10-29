"""Original published Roots: real entered N=25, R=2 and native 5^2=25.

One completed custom-root calculation. A later Q / STOP and shell restoration
are NOT established; neither numeric accuracy for other inputs nor all menus.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'src/zx-ux-sdk'), str(Path(__file__).resolve().parent)]
import rld
import rvm
from test_native_oxo_complete_round import text_row

GAME = ROOT/'src/bonus/60-programs/56-roots'
BAS, TZX = (GAME/'BASIC/56-roots.bas', GAME/'BASIC/56-roots.tzx')
SSX = GAME/'bin/56-roots.ssx'
FONT = ROOT/'build/tmp/rbc-recovered/rbc/font32.bin'
ROM = ROOT/'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT/'build/out/ZX-UX.tzx'
FROZEN = ROOT/'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, ROM, SYSTEM, FROZEN))
KEYS = ('{WAIT 350}{ENTER}{WAIT 200}{ENTER}{WAIT 200}{ENTER}'
        '{WAIT 240}{ENTER}{WAIT 150}25{ENTER}{WAIT 100}2{ENTER}')


@unittest.skipUnless(READY, 'published native Roots and checked 48K system required')
class NativeRootsCustomCalculation(unittest.TestCase):
    def test_original_calculates_sqrt25_from_keyboard(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        source = tuple(p.read_bytes() for p in (BAS, TZX, SSX, ROM))
        self.assertIn(b'700 PRINT INVERSE 1;AT 8,0', source[0])
        self.assertIn(b'710 PRINT AT 13,0', source[0])
        self.assertIn(b'730 INPUT', source[0])
        parsed = rld.parse_ssx(source[2])
        self.assertEqual(parsed['entry'], 0)
        self.assertLessEqual(max(len(source[2]),len(parsed['image'])+
                                 parsed['bss']+parsed['stack']),14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font),768)
        # Both are authentic ZX-UX kernel runs, with only keyboard events varied.
        quiet = rvm.run_kernel(SSX, keys='{WAIT 350}{ENTER}', frames=700, system=SYSTEM)
        prior, _ = quiet.picture()
        self.assertEqual(len(prior),6912)
        played = rvm.run_kernel(SSX, keys=KEYS, frames=2000, system=SYSTEM)
        self.assertIsNotNone(played.fg.started)
        self.assertIsNone(played.fg.ended)
        self.assertTrue(played.session.owns_screen(played.fg.pid))
        pic, border = played.picture()
        self.assertEqual(len(pic),6912)
        self.assertIn('ENTER NUMBER (N): 25',text_row(pic,1,font))
        self.assertIn(': ROOT NUMBER = 2',text_row(pic,3,font))
        self.assertIn('THE 2 ROOT OF 25 IS',text_row(pic,8,font))
        self.assertEqual(text_row(pic,9,font).strip(),'5')
        self.assertIn('5 ^ 2 = 25',text_row(pic,15,font))
        self.assertIn("ENTER 'Q' TO QUIT",text_row(pic,21,font))
        self.assertNotEqual(hashlib.sha256(prior).digest(),
                            hashlib.sha256(pic).digest())
        if os.environ.get('RBC_ROOTS_CAPTURE_DIR'):
            folder=Path(os.environ['RBC_ROOTS_CAPTURE_DIR'])
            folder.mkdir(parents=True,exist_ok=True)
            rvm.write_png(pic,str(folder/'roots-25-square-calculated.png'),border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS,TZX,SSX,ROM)),source)


if __name__ == '__main__':
    unittest.main()
