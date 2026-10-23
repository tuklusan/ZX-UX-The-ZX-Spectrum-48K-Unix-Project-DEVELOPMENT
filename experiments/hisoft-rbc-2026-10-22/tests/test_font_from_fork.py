"""Tests for the bit order and size of the printable font."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from font_from_fork import build_font


class TestFont(unittest.TestCase):
    def test_128_characters_and_correct_bit_order(self):
        glyphs = ['{ ' + ', '.join('0x00' for _ in range(8)) + ' }'] * 128
        glyphs[65] = '{ 0x0C, 0x1E, 0x33, 0x00, 0x00, 0x00, 0x00, 0x00 }'
        font = build_font('\n'.join(glyphs))
        self.assertEqual(len(font), 768)
        self.assertEqual(font[(65 - 32) * 8:(65 - 32) * 8 + 3], b'\x30\x78\xcc')


if __name__ == '__main__':
    unittest.main()
