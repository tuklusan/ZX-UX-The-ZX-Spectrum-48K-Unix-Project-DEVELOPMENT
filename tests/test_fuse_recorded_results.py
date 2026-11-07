"""Recorded native outcomes may settle without repeating motion."""
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/tools'))
from capture_quality import recorded_result_frame


def screen(shift=0, *, result=False):
    image = Image.new('RGB', (320, 240), 'black')
    canvas = ImageDraw.Draw(image)
    canvas.rectangle((50, 50, 160, 60), fill='white')
    if result:
        canvas.rectangle((75 + shift, 100, 120 + shift, 130), fill='green')
        canvas.rectangle((128, 150, 175, 164), fill='white')
    return image


class RecordedResultTests(unittest.TestCase):
    def test_random_result_positions_are_not_fixed(self):
        boot = Image.new('RGB', (320, 240), 'black')
        before = screen()
        for shift in (0, 24, 50):
            with self.subTest(position=shift):
                outcome = screen(shift, result=True)
                picked = recorded_result_frame([before, outcome] + [outcome] * 4,
                                               before, boot, before)
                self.assertIsNotNone(picked)
                self.assertEqual(picked.tobytes(), outcome.tobytes())

    def test_unobserved_or_unchanged_result_is_refused(self):
        boot = Image.new('RGB', (320, 240), 'black')
        before = screen()
        self.assertIsNone(recorded_result_frame([before] * 10,
                                                before, boot, before))
        self.assertIsNone(recorded_result_frame([before], before, boot, before))
        self.assertIsNone(recorded_result_frame([boot] * 6, before, boot, before))

    def test_single_transition_is_not_a_settled_result(self):
        boot = Image.new('RGB', (320, 240), 'black')
        before = screen()
        result = screen(20, result=True)
        self.assertIsNone(recorded_result_frame([before, result, before, result],
                                                before, boot, before))


if __name__ == '__main__':
    unittest.main()
