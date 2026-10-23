"""Check real ZX-UX keyboard-matrix scheduling across interrupt scans.

These host-side checks do not replace end-to-end INKEY$ execution tests.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dist/sdk/bin/py'))
try:
    import zxux
except ImportError:
    zxux = None


@unittest.skipIf(zxux is None, 'native keyboard model absent from isolated tests')
class KeyboardMatrixTests(unittest.TestCase):
    def test_no_key_is_immediate_and_unbuffered(self):
        keyboard = zxux.Keyboard()
        for frame in range(80):
            self.assertEqual(keyboard.tick(frame), ())
            self.assertFalse(keyboard.busy())

    def test_press_hold_release_and_quiet_frames(self):
        keyboard = zxux.Keyboard()
        combo = zxux.char_keys('z')
        keyboard.add([('press', combo, 25)])
        self.assertEqual(keyboard.tick(100), combo)
        for frame in range(101, 125):
            self.assertEqual(keyboard.tick(frame), combo)
        for frame in range(125, 145):
            self.assertEqual(keyboard.tick(frame), ())
        self.assertFalse(keyboard.busy())

    def test_repeat_cannot_bypass_release_settle(self):
        keyboard = zxux.Keyboard()
        combo = zxux.char_keys('8')
        keyboard.add([('press', combo, 3), ('press', combo, 3)])
        observed = [bool(keyboard.tick(frame)) for frame in range(40)]
        blocks = []
        in_block = False
        for index, held in enumerate(observed):
            if held and not in_block:
                blocks.append([index, index])
                in_block = True
            elif held:
                blocks[-1][1] = index
            else:
                in_block = False
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][1] - blocks[0][0] + 1, 3)
        self.assertEqual(blocks[1][1] - blocks[1][0] + 1, 3)
        self.assertGreaterEqual(blocks[1][0] - blocks[0][1] - 1,
                                keyboard.SETTLE - 1)


if __name__ == '__main__':
    unittest.main()
