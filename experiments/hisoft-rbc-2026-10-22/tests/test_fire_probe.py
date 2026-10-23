"""Check deterministic screen-beam and score extraction."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from fire_probe import beam_pixels, displayed_score


class FireProbeTests(unittest.TestCase):
    def test_screen_beam_column(self):
        screen = bytearray(6912)
        self.assertEqual(beam_pixels(screen), 0)
        for y in range(40, 180):
            at = ((y & 192) << 5) | ((y & 7) << 8) | ((y & 56) << 2) | 17
            screen[at] = 1
        self.assertEqual(beam_pixels(screen), 140)

    def test_scores_do_not_confuse_high_score(self):
        self.assertEqual(displayed_score('SCORE:40        HIGH-SCORE:0'), 40)
        self.assertEqual(displayed_score('                 HIGH-SCORE:80'), 0)
        self.assertEqual(displayed_score('SCORE:0'), 0)

    def test_invalid_bitmap_rejected(self):
        with self.assertRaises(ValueError):
            beam_pixels(b'')


if __name__ == '__main__':
    unittest.main()
