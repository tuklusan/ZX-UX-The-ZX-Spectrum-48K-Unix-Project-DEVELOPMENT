"""Check the unchanged published WordSum's reveal and fresh-round input in ZX-UX."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).resolve().parent)]
import rld
import rvm
from test_native_oxo_complete_round import text_row

GAME = ROOT / 'src/bonus/60-programs/40-wordsum'
BAS = GAME / 'BASIC/40-wordsum.bas'
TZX = GAME / 'BASIC/40-wordsum.tzx'
SSX = GAME / 'bin/40-wordsum.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (BAS, TZX, SSX, FONT, SYSTEM, FROZEN))
REVEAL = '{WAIT 500}{SPACE}'
REPLAY = REVEAL + '{WAIT 350}1'


@unittest.skipUnless(READY, 'published WordSum, recovered font and native kernel required')
class NativeWordSumRevealReplay(unittest.TestCase):
    def test_space_reveals_word_and_one_starts_fresh_puzzle(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        originals = tuple(p.read_bytes() for p in (BAS, TZX, SSX))
        native = rld.parse_ssx(originals[2])
        self.assertEqual(native['entry'], 0)
        self.assertLessEqual(max(len(originals[2]), len(native['image']) +
                                 native['bss'] + native['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)
        words = set(re.findall(r'"([A-Z]{5,6})"', BAS.read_text(encoding='ascii')))
        self.assertIn('HEARTH', words)

        cases = (('initial', '', 1100), ('revealed', REVEAL, 1100),
                 ('replayed', REPLAY, 1900))
        screens = {}
        for name, keys, frames in cases:
            with self.subTest(screen=name):
                run = rvm.run_kernel(SSX, keys=keys, frames=frames,
                                     system=SYSTEM)
                self.assertEqual(run.why, 'frames', run.summary())
                self.assertIsNotNone(run.fg.started)
                self.assertIsNone(run.fg.ended)
                self.assertTrue(run.session.owns_screen(run.fg.pid))
                screen, border = run.picture()
                self.assertEqual(len(screen), 6912)
                screens[name] = screen
                if os.environ.get('RBC_WORDSUM_CAPTURE_DIR'):
                    dest = Path(os.environ['RBC_WORDSUM_CAPTURE_DIR'])
                    dest.mkdir(parents=True, exist_ok=True)
                    rvm.write_png(screen, str(dest / ('wordsum-' + name + '.png')),
                                  border)

        initial, revealed, replayed = (screens[n] for n, _, _ in cases)
        self.assertEqual(text_row(initial, 18, font).strip(),
                         'PRESS <SPACE> TO REVEAL THE WORD')
        self.assertEqual(text_row(revealed, 18, font).strip(),
                         'PRESS <1> FOR ANOTHER WORDSUM')
        self.assertNotEqual(hashlib.sha256(initial).digest(),
                            hashlib.sha256(revealed).digest())
        revealed_word = ''.join(re.findall(r'[A-Z]', text_row(revealed, 12, font)))
        self.assertIn(revealed_word, words)
        self.assertEqual(text_row(replayed, 18, font).strip(),
                         'PRESS <SPACE> TO REVEAL THE WORD')
        self.assertNotEqual(hashlib.sha256(revealed).digest(),
                            hashlib.sha256(replayed).digest())
        self.assertNotEqual(text_row(initial, 12, font),
                            text_row(replayed, 12, font))
        self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, SSX)),
                         originals)


if __name__ == '__main__':
    unittest.main()
