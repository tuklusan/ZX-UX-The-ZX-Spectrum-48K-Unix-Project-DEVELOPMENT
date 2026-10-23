"""Check reuse of the existing HiSoft computed-line search flags."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from computed_lines import compiler_with_computed_lines


class ComputedLineTests(unittest.TestCase):
    def test_upstream_reset_is_preserved(self):
        class Base:
            def reset(self, program):
                self.program = program
                self.goto_directive = 0
                self.gosub_all = 0
                self.restore_directive = 0
                self.restore_all = 0

        instance = compiler_with_computed_lines(Base)()
        instance.reset(b'example')
        self.assertEqual(instance.program, b'example')
        self.assertEqual(instance.goto_directive, 1)
        self.assertEqual(instance.gosub_all, 1)
        self.assertEqual(instance.restore_directive, 1)
        self.assertEqual(instance.restore_all, 1)
        instance.reset(b'other')
        self.assertEqual(instance.goto_directive, 1)

    def test_original_base_class_is_not_changed(self):
        class Base:
            def reset(self, program):
                self.goto_directive = 0
                self.gosub_all = 0
                self.restore_directive = 0
                self.restore_all = 0

        enabled = compiler_with_computed_lines(Base)()
        normal = Base()
        enabled.reset(b'')
        normal.reset(b'')
        self.assertEqual((enabled.goto_directive, enabled.gosub_all), (1, 1))
        self.assertEqual((normal.goto_directive, normal.gosub_all), (0, 0))
        self.assertEqual((enabled.restore_directive, enabled.restore_all), (1, 1))
        self.assertEqual((normal.restore_directive, normal.restore_all), (0, 0))


if __name__ == '__main__':
    unittest.main()
