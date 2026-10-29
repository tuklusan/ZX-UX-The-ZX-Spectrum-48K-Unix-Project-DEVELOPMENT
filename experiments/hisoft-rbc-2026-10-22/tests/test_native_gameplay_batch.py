"""Fail-closed bounded real-ZX-UX batch tests."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_gameplay_batch import classify, parse_args, run_one, save_result
from native_gameplay_34 import FRAME_LIMITS, SCRIPTS


class NativeGameplayBatchClassification(unittest.TestCase):
    def test_changed_and_unverified_are_distinct(self):
        good = ('42-bricklayer: DISPLAY CHANGED [frames/frames]\n'
                'LIVE ZX-UX: 1 loaded; 1 display changes; '
                '0 input effects not proven\n')
        still = ('42-bricklayer: INPUT EFFECT UNVERIFIED [frames/input]\n'
                 'LIVE ZX-UX: 1 loaded; 0 display changes; '
                 '1 input effects not proven\n')
        self.assertTrue(classify('42-bricklayer', 0, good, '').startswith('DISPLAY'))
        self.assertTrue(classify('42-bricklayer', 1, still, '').startswith('SCREEN'))
        for code, out in ((1, good), (0, still), (0, ''),
                          (0, good + good), (0, good.replace('42-', '43-'))):
            with self.subTest(code=code, out=out[:20]):
                self.assertTrue(classify('42-bricklayer', code, out, '').startswith('ERROR'))

    def test_source_guided_inkey_game_timings(self):
        self.assertEqual(FRAME_LIMITS['14-scuba'], 2400)
        self.assertEqual(FRAME_LIMITS['54-swordsman'], 620)
        self.assertEqual(SCRIPTS['14-scuba'], '{WAIT 1600}{ENTER}{WAIT 120}x')
        self.assertEqual(SCRIPTS['54-swordsman'], '{WAIT 250}Y')

    def test_two_hour_runner_five_minute_game_twelve_parallel(self):
        args = parse_args([])
        self.assertEqual(args.timeout, 300)
        self.assertEqual(args.runner_timeout, 7200)
        self.assertEqual(args.jobs, 12)
        self.assertEqual(args.batch_size, 12)
        with self.assertRaises(SystemExit):
            parse_args(['--timeout', '301'])
        with self.assertRaises(SystemExit):
            parse_args(['--batch-size', '13'])
        with self.assertRaises(SystemExit):
            parse_args(['--runner-timeout', '7201'])
        with self.assertRaises(SystemExit):
            parse_args(['--results-dir', '/tmp/invalid-gameplay-reports'])

    def test_preserve_timeout_output_and_refuse_overwrite(self):
        with patch('native_gameplay_batch.subprocess.run',
                   side_effect=subprocess.TimeoutExpired(['python'], 300,
                                                        output=b'partial\n', stderr=b'why\n')):
            game, status, code, stdout, stderr = run_one('42-bricklayer', 300)
        self.assertEqual(game, '42-bricklayer')
        self.assertEqual(status, 'TIMEOUT (unverified)')
        self.assertIsNone(code)
        with tempfile.TemporaryDirectory() as tmp:
            save_result(Path(tmp), game, status, code, stdout, stderr)
            saved = (Path(tmp) / (game + '.log')).read_text()
            self.assertIn('partial\n', saved)
            self.assertIn('why\n', saved)
            self.assertIn('TIMEOUT', saved)
            with self.assertRaises(FileExistsError):
                save_result(Path(tmp), game, status, code, stdout, stderr)


if __name__ == '__main__':
    unittest.main()
