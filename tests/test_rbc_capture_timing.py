"""Apply tape-input timing only when matching recorded keys."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'build/tools'), str(ROOT / 'dist/sdk/bin/py')]
from capture_replay import steps, recorded_first_input_wait
from capture_quality import moving_replay_frame
from PIL import Image, ImageDraw


class TimedReplayTests(unittest.TestCase):
    def test_measured_waits_from_original_guides(self):
        for program, expected in [('06-motocross', 713),
                                  ('24-aben', 229),
                                  ('30-space-traffic', 278)]:
            with self.subTest(program=program):
                recorded = steps('60-programs', program)
                self.assertTrue(any(step[0] == 'C' for step in recorded))
                self.assertEqual(recorded_first_input_wait('60-programs', program,
                                                           recorded), expected)

    def test_persistent_native_motion_beats_menu_frames(self):
        boot = Image.new('RGB', (320, 240), 'black')
        shell = boot.copy()
        ImageDraw.Draw(shell).rectangle((50, 52, 140, 80), fill='white')
        menu = shell.copy()
        ImageDraw.Draw(menu).rectangle((52, 95, 170, 115), fill='white')
        frames = [menu.copy() for _ in range(3)]
        for offset in range(7):
            frame = boot.copy()
            canvas = ImageDraw.Draw(frame)
            canvas.rectangle((65 + offset * 3, 85, 75 + offset * 3, 95), fill='yellow')
            canvas.rectangle((120 - offset * 2, 120, 130 - offset * 2, 130), fill='white')
            frames.append(frame)
        frames.extend(menu.copy() for _ in range(4))
        chosen = moving_replay_frame(frames, boot, shell)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.tobytes(), frames[9].tobytes())
        self.assertIsNone(moving_replay_frame(frames[:3], boot, shell))
        self.assertIsNone(moving_replay_frame([menu] * 10, boot, shell))

    def test_console_cursor_and_taskbar_are_not_gameplay(self):
        boot = Image.new('RGB', (320, 240), 'black')
        samples = []
        for offset in range(9):
            frame = boot.copy()
            canvas = ImageDraw.Draw(frame)
            canvas.rectangle((38, 38, 180, 55), fill='white')
            canvas.rectangle((45 + 2 * offset, 95, 58 + 2 * offset, 103),
                             fill='white')
            canvas.rectangle((32, 203, 120, 213), fill='yellow')
            samples.append(frame)
        self.assertIsNone(moving_replay_frame(samples, boot, boot))

    def test_richer_moving_frame_beats_late_sparse_frame(self):
        boot = Image.new('RGB', (320, 240), 'black')
        frames = []
        for index in range(14):
            frame = boot.copy()
            canvas = ImageDraw.Draw(frame)
            canvas.rectangle((50 + index * 3, 80, 64 + index * 3, 95), fill='yellow')
            canvas.rectangle((165 - index * 3, 125, 179 - index * 3, 139), fill='white')
            if index < 9:
                canvas.rectangle((80, 42, 136, 53), fill='green')
            frames.append(frame)
        chosen = moving_replay_frame(frames, boot, boot)
        self.assertIsNotNone(chosen)
        self.assertIn(chosen.tobytes(), [image.tobytes() for image in frames[4:9]])

    def test_no_unrecorded_wait_is_invented(self):
        for program in ('39-compspacegames-SpaceGames-11', '50-monsters--Monsters'):
            with self.subTest(program=program):
                recorded = steps('www.thespectrumshow.net', program)
                self.assertIsNone(recorded_first_input_wait('www.thespectrumshow.net',
                                                            program, recorded))
        self.assertIsNone(recorded_first_input_wait('not-a-collection', 'missing', ()))


if __name__ == '__main__':
    unittest.main()
