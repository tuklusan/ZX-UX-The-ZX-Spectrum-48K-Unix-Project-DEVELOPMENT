"""Pure frame decoder checks; no emulator or compiler is needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from frame_probe import screen_cell, screen_letters


class FrameDecoderTests(unittest.TestCase):
    def test_interleaved_screen_cell_round_trip(self):
        screen = bytearray(6912)
        font = bytearray(768)
        # Character A: 8 distinct row bytes across the odd ZX bitmap order.
        rows = bytes((24, 36, 66, 126, 66, 66, 66, 0))
        font[(65 - 32) * 8:(66 - 32) * 8] = rows
        for y, byte in enumerate(rows):
            scan = 8 * 10 + y
            offset = ((scan & 0xC0) << 5) | ((scan & 7) << 8) | ((scan & 0x38) << 2) | 9
            screen[offset] = byte
        self.assertEqual(screen_cell(screen, 10, 9), rows)
        self.assertEqual(screen_letters(screen, font)[10][9], 'A')

    def test_reject_invalid_source_lengths(self):
        with self.assertRaises(ValueError):
            screen_cell(b'', 0, 0)
        with self.assertRaises(ValueError):
            screen_letters(bytes(6912), bytes(767))
        with self.assertRaises(ValueError):
            screen_cell(bytes(6912), 24, 0)


if __name__ == '__main__':
    unittest.main()
