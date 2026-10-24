"""Dynamic 48K FOR/NEXT control semantics, independent of line ordering."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from spectrum_loops import ProcessLoopStack

class LoopSemantics(unittest.TestCase):
    def setUp(self):
        self.m = ProcessLoopStack()

    def test_lowercase_control_and_modified_value(self):
        self.assertTrue(self.m.enter('i', 1, 10, 1, 345))
        self.m.assign('I', 8)
        self.assertEqual(self.m.next('i'), 345)
        self.assertEqual(self.m.value('I'), 9)

    def test_absent_compiletime_next(self):
        self.m.enter('i', 1, 5, 1, 100)
        self.assertEqual(self.m.next('i'), 100)

    def test_jump_never_invalidates_control(self):
        self.m.enter('i', 1, 3, 1, 100)
        self.m.jump(900)
        self.assertEqual(self.m.next('i'), 100)

    def test_negative_step_and_completion(self):
        self.assertTrue(self.m.enter('n', 9, 1, -3, 201))
        self.assertEqual(self.m.next('n'), 201)
        self.assertEqual(self.m.next('n'), 201)
        self.assertEqual(self.m.next('n'), None)
        self.assertEqual(self.m.value('n'), 0)

    def test_zero_iteration_positive_and_negative(self):
        self.assertFalse(self.m.enter('i', 10, 1, 1, 200))
        self.assertFalse(self.m.enter('j', 1, 10, -1, 100))

    def test_repeated_for_replaces_control(self):
        self.m.enter('i', 1, 10, 1, 300)
        self.m.enter('i', 40, 50, 2, 400)
        self.assertEqual(self.m.next('i'), 400)
        self.assertEqual(self.m.value('i'), 42)

    def test_different_variables_maintain_independent_records(self):
        self.m.enter('i', 1, 5, 1, 100)
        self.m.enter('j', 2, 6, 2, 400)
        self.assertEqual(self.m.next('i'), 100)
        self.assertEqual(self.m.next('j'), 400)

    def test_next_after_completion_runtime_error(self):
        self.m.enter('i', 1, 1, 1, 100)
        self.assertIsNone(self.m.next('i'))
        with self.assertRaisesRegex(ValueError, 'NEXT without FOR'):
            self.m.next('i')

    def test_run_invalidates_records(self):
        self.m.enter('i', 1, 2, 1, 10)
        self.m.run()
        with self.assertRaisesRegex(ValueError,'NEXT without FOR'):
            self.m.next('i')

if __name__ == '__main__':
    unittest.main()
