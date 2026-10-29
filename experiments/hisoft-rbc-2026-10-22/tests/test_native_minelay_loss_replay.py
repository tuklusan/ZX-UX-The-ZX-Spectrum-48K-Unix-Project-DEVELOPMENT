"""Original Minelay: native three-life maze loss and easier-game replay.

Use only original published BAS, TZX, SSX, checked ROM, real ZX-UX loader
and physical emulator keyboard events. This is not a victory or a mine-clear
proof; the low-score losing branch and restart are checked.
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

GAME = ROOT/'src/bonus/60-programs/01-minelay'
BAS = GAME/'BASIC/01-minelay.bas'
TZX = GAME/'BASIC/01-minelay.tzx'
SSX = GAME/'bin/01-minelay.ssx'
ROM = ROOT/'src/zx-ux-sdk/rom/48.rom'
FONT = ROOT/'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT/'build/out/ZX-UX.tzx'
FROZEN = ROOT/'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS,TZX,SSX,ROM,FONT,SYSTEM,FROZEN))


@unittest.skipUnless(READY, 'checked originals, ROM and ZX-UX system required')
class NativeMinelayLossReplay(unittest.TestCase):
    def test_natural_maze_loss_and_easier_game_restart(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        original = tuple(p.read_bytes() for p in (BAS,TZX,SSX,ROM))
        self.assertIn(b'6020 CLS : PRINT AT 5,8',original[0])
        self.assertIn(b'6030 PRINT INK 6',original[0])
        self.assertIn(b'6040 IF INKEY$',original[0])
        layout = rld.parse_ssx(original[2])
        self.assertEqual(layout['entry'],0)
        self.assertLessEqual(max(len(original[2]),len(layout['image']) +
                                 layout['bss'] + layout['stack']),14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font),768)
        keys='{WAIT 250}{ENTER}{WAIT 100}{ENTER}{WAIT 150}2'
        run=rvm.run_kernel(SSX,keys=keys,frames=5000,system=SYSTEM)
        self.assertEqual(run.why,'frames',run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        lost,lost_border=run.picture()
        self.assertEqual(len(lost),6912)
        self.assertEqual(text_row(lost,5,font).strip(),'G A M E  O V E R')
        self.assertEqual(text_row(lost,8,font).strip(),'You scored 0')
        self.assertEqual(text_row(lost,11,font).strip(),'The high-score is 0')
        self.assertIn('Press 1 for a hard game, or 2',text_row(lost,16,font))
        self.assertIn('for an easier game.',text_row(lost,17,font))

        run.session.kb.type('2')
        for _ in range(450):
            run.frame()
        fresh,fresh_border=run.picture()
        self.assertEqual(len(fresh),6912)
        self.assertTrue(text_row(fresh,0,font).strip().startswith('Score 0'))
        self.assertIn('Hi-score 0',text_row(fresh,0,font))
        self.assertNotIn('G A M E  O V E R',text_row(fresh,5,font))
        self.assertNotEqual(hashlib.sha256(lost).digest(),
                            hashlib.sha256(fresh).digest())
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        if os.environ.get('RBC_MINELAY_CAPTURE_DIR'):
            out=Path(os.environ['RBC_MINELAY_CAPTURE_DIR'])
            out.mkdir(parents=True,exist_ok=True)
            rvm.write_png(lost,str(out/'minelay-gameover.png'),lost_border)
            rvm.write_png(fresh,str(out/'minelay-replayed.png'),fresh_border)
        self.assertEqual(tuple(p.read_bytes() for p in
                               (BAS,TZX,SSX,ROM)),original)


if __name__ == '__main__':
    unittest.main()
