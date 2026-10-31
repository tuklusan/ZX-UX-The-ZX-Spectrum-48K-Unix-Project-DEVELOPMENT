"""Gallery replay recipes come only from recorded BASIC controls."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'build/tools'), str(ROOT / 'dist/sdk/bin/py')]
from capture_replay import COLLECTIONS, steps, key, rvm_actions, fuse_steps


class RecordedCaptureTests(unittest.TestCase):
    def test_all_accepted_binaries_have_parseable_controls(self):
        collection = COLLECTIONS / '60-programs'
        accepted = sorted(p for p in collection.iterdir() if (p / 'bin' / (p.name + '.ssx')).is_file())
        self.assertEqual(len(accepted), 34)
        for game in accepted:
            with self.subTest(game=game.name):
                script = steps('60-programs', game.name)
                self.assertTrue(script)
                self.assertTrue(rvm_actions(script))
                self.assertTrue(fuse_steps(script))

    def test_line_hold_and_shift_are_reproduced(self):
        case = (('L', '10'), ('H', 'Return', .7), ('S', 'n'), ('K', 'space'), ('C', 'checkpoint'))
        self.assertEqual(fuse_steps(case), [(0.65, '10\n'), (0.65, '\n', .7),
                                            (0.65, 'N'), (0.65, ' '), (0.5, '')])
        actions = rvm_actions(case)
        self.assertIn(('press', ('ENTER',), 35), actions)
        self.assertIn(('keys', ('CS', 'n')), actions)
        self.assertEqual(key('space'), ' ')

    def test_missing_collection_not_taken_as_compiled(self):
        self.assertEqual(steps('not-a-real-collection', '01-test'), ())


if __name__ == '__main__':
    unittest.main()
