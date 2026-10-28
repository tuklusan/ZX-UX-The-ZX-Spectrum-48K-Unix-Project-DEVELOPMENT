"""Original OXO: play a complete native round, score it, restart the board.

Use the published SSX unchanged, the real ZX-UX loader, and actual keyboard
frames. The recorded win is the computer's, not a synthetic game result.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm

GAME = ROOT / 'src/bonus/60-programs/29-oxo'
SOURCE = GAME / 'BASIC/29-oxo.bas'
TAPE = GAME / 'BASIC/29-oxo.tzx'
NATIVE = GAME / 'bin/29-oxo.ssx'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (SOURCE, TAPE, NATIVE, FONT, SYSTEM, FROZEN))
MOVES = '{WAIT 250}' + '{WAIT 45}'.join('123456789123456789')


def text_row(screen: bytes, y: int, font: bytes) -> str:
    """Decode actual ULA pixels against the delivered original 8x8 font."""
    if len(screen) != 6912 or len(font) != 768 or not 0 <= y < 24:
        raise ValueError('invalid original screen or font geometry')
    known = {font[i*8:(i+1)*8]: chr(i+32) for i in range(96)}
    result = []
    for x in range(32):
        glyph = bytes(screen[(((y*8+i) & 0xc0) << 5) |
                             (((y*8+i) & 7) << 8) |
                             (((y*8+i) & 0x38) << 2) | x]
                      for i in range(8))
        inverse = bytes(b ^ 0xff for b in glyph)
        result.append(known.get(glyph, known.get(inverse, '?')))
    return ''.join(result)


@unittest.skipUnless(READY, 'requires original OXO inputs, linked SSX and ZX-UX')
class NativeOxoCompleteRound(unittest.TestCase):
    def test_computer_win_tally_and_new_board(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        tape_hash = hashlib.sha256(TAPE.read_bytes()).hexdigest()
        native = NATIVE.read_bytes()
        parsed = rld.parse_ssx(native)
        self.assertEqual(parsed['entry'], 0)
        self.assertLessEqual(max(len(native), len(parsed['image']) +
                                 parsed['bss'] + parsed['stack']), 14000)
        font = FONT.read_bytes()
        self.assertEqual(len(font), 768)

        result = rvm.run_kernel(NATIVE, keys=MOVES, frames=2400, system=SYSTEM)
        self.assertEqual(result.why, 'frames', result.summary())
        self.assertIsNotNone(result.fg.started)
        self.assertIsNone(result.fg.ended)
        self.assertTrue(result.session.owns_screen(result.fg.pid))
        picture, _ = result.picture()
        self.assertEqual(text_row(picture, 19, font).strip(), 'I WIN')
        self.assertIn('Score: You 0   Me 3    Draw 0',
                      text_row(picture, 20, font))
        self.assertIn('Press any key for new game',
                      text_row(picture, 21, font))

        replay = rvm.run_kernel(NATIVE, keys=MOVES + '{WAIT 1650}a',
                                frames=3600, system=SYSTEM)
        self.assertEqual(replay.why, 'frames', replay.summary())
        self.assertIsNotNone(replay.fg.started)
        self.assertIsNone(replay.fg.ended)
        self.assertTrue(replay.session.owns_screen(replay.fg.pid))
        following, _ = replay.picture()
        self.assertNotEqual(picture, following)
        self.assertEqual(text_row(following, 19, font).strip(), '')
        self.assertNotIn('Press any key for new game',
                         text_row(following, 21, font))
        self.assertIn('to go FIRST', text_row(following, 2, font))
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), source_hash)
        self.assertEqual(hashlib.sha256(TAPE.read_bytes()).hexdigest(), tape_hash)
        self.assertEqual(NATIVE.read_bytes(), native)


if __name__ == '__main__':
    unittest.main()
