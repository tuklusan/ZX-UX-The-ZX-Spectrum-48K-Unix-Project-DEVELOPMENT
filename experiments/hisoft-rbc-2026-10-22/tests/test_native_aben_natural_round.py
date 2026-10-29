"""Original Aben: reach its three-wave end prompt in the real ZX-UX loader.

This is a source-guided bounded result, not an INPUT or replay proof.
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

GAME = ROOT / 'src/bonus/60-programs/24-aben'
BAS = GAME / 'BASIC/24-aben.bas'
TZX = GAME / 'BASIC/24-aben.tzx'
SSX = GAME / 'bin/24-aben.ssx'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
READY = all(p.is_file() for p in (BAS, TZX, SSX, SYSTEM, FROZEN, FONT))
KEYS = '{WAIT 200}v{WAIT 350}a'


@unittest.skipUnless(READY, 'checked real ZX-UX kernel and original font required')
class NativeAbenNaturalRound(unittest.TestCase):
    def test_original_three_wave_prompt_without_assuming_replay(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        self.assertIn(b'IF c=3 THEN GO TO 305', originals[0])
        self.assertIn(b'Do you want to see the alien?', originals[0])
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        self.assertEqual(hashlib.sha256(font).hexdigest(),
                         '7b8faa46ee8359ea1cf141a85f618f9f3716334495f3c5c107bb1e5cb86cc468')
        linked = rld.parse_ssx(originals[2])
        self.assertEqual(linked['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(linked['image']) +
                                 linked['bss'] + linked['stack']), 14000)
        run = rvm.run_kernel(SSX, keys=KEYS, frames=5000, system=SYSTEM)
        self.assertEqual(run.why, 'frames', run.summary())
        self.assertIsNotNone(run.fg.started)
        self.assertIsNone(run.fg.ended)
        self.assertTrue(run.session.owns_screen(run.fg.pid))
        image, border = run.picture()
        self.assertEqual(len(image), 6912)
        self.assertIn('SCORE:0', text_row(image, 0, font))
        self.assertIn('HI-SCORE:0', text_row(image, 0, font))
        self.assertIn('Do you want to see the alien?', text_row(image, 22, font))
        if os.environ.get('RBC_ABEN_CAPTURE_DIR'):
            target = Path(os.environ['RBC_ABEN_CAPTURE_DIR'])
            target.mkdir(parents=True, exist_ok=True)
            rvm.write_png(image, str(target / 'aben-three-wave-prompt.png'), border)
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)), originals)


if __name__ == '__main__':
    unittest.main()
