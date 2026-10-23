"""Pure frame decoder checks; no emulator or compiler is needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from frame_probe import screen_cell, screen_letters, GAME_KEY_PLAN, check_udgs


class FrameDecoderTests(unittest.TestCase):
    def test_key_sequences_follow_original_basic(self):
        self.assertEqual(GAME_KEY_PLAN['25-galaxians'], ('z', 'x', 'm'))
        self.assertEqual(GAME_KEY_PLAN['58-invaders'], ('5', '8', '0'))

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

    def test_udg_pointer_and_original_sprite_bytes(self):
        memory = bytearray(65536)
        base = 42000
        rows = ((0xA2, (60, 140, 115, 51, 63, 111, 193, 192)),
                (0x98, (60, 49, 206, 204, 252, 246, 131, 3)))
        for code, glyph in rows:
            start = base + (code - 0x90) * 8
            memory[start:start + 8] = bytes(glyph)
        result = check_udgs(memory, base, '58-invaders')
        self.assertEqual(len(result), 2)
        self.assertTrue(all(item['matches_original_data'] for item in result))
        memory[base + (0x98 - 0x90) * 8] = 0
        broken = check_udgs(memory, base, '58-invaders')
        self.assertFalse(all(item['matches_original_data'] for item in broken))

    def test_reject_invalid_source_lengths(self):
        with self.assertRaises(ValueError):
            screen_cell(b'', 0, 0)
        with self.assertRaises(ValueError):
            screen_letters(bytes(6912), bytes(767))
        with self.assertRaises(ValueError):
            screen_cell(bytes(6912), 24, 0)


if __name__ == '__main__':
    unittest.main()
