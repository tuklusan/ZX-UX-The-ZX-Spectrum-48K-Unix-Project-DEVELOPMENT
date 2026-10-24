"""Spectrum loop stack semantics, including jumps and modified counters."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))


class Round2Loops(unittest.TestCase):
    def runtime(self):
        from spectrum_loops import ProcessLoopStack
        return ProcessLoopStack()

    def test_next_uses_current_variable_value(self):
        loop = self.runtime()
        loop.enter('I', 1, 10, 1, 100)
        loop.assign('I', 8)
        self.assertEqual(loop.next('I'), 100)
        self.assertEqual(loop.value('I'), 9)

    def test_for_has_no_required_static_next(self):
        loop = self.runtime()
        loop.enter('I', 1, 3, 1, 30)
        self.assertEqual(loop.value('I'), 1)
        self.assertEqual(loop.next('I'), 30)

    def test_computed_jump_does_not_corrupt_loop_state(self):
        loop = self.runtime()
        loop.enter('J', 1, 2, 1, 100)
        loop.jump(900)
        self.assertEqual(loop.next('J'), 100)

    def test_missing_runtime_next_reports_spectrum_error(self):
        loop = self.runtime()
        with self.assertRaises(ValueError):
            loop.next('I')

    def test_run_resets_runtime_loop_stack(self):
        loop = self.runtime()
        loop.enter('I', 1, 2, 1, 20)
        loop.run()
        with self.assertRaises(ValueError):
            loop.next('I')


if __name__ == '__main__':
    unittest.main()
