"""Regression cases for Sinclair BASIC's missing-line jump behavior."""
import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))


def split_lines(program):
    return [(int(n), bytes.fromhex(hex_body)) for n, hex_body in program]


def join_lines(rows):
    return list(rows)


tap = types.ModuleType('tap')
tap.split_lines = split_lines
tap.join_lines = join_lines
sys.modules['tap'] = tap
source = types.ModuleType('source')
source.hide_numbers = lambda number, fp: number + b'\x0e12345'
sys.modules['source'] = source
import line_targets


class Keys:
    CODE_FOR = {'GO TO': 0xec, 'GO SUB': 0xed, 'REM': 0xea}


def make(*rows):
    return [(n, body.hex()) for n, body in rows]


class TestMissingLines(unittest.TestCase):
    def test_go_sub_enters_next_existing_line(self):
        src = make((50, b'\xed70\x0e00000:\xed220\x0e00000\r'),
                   (100, b'\xf5"HI"\r'), (220, b'\xc9\r'))
        result, changes = line_targets.resolve_missing_targets(src, Keys, None)
        self.assertEqual(changes, [(50, 70, 100)])
        self.assertIn(b'\xed100\x0e12345:', result[0][1])
        self.assertIn(b'\xed220\x0e00000', result[0][1])

    def test_ignore_literals_comments_and_computed_targets(self):
        src = make((10, b'\xf5"\xed70\x0e00000":\xea\xed70\x0e00000\r'),
                   (20, b'\xec70\x0e00000+X\r'), (100, b'\xf5"OK"\r'))
        result, changes = line_targets.resolve_missing_targets(src, Keys, None)
        self.assertEqual(changes, [])
        self.assertEqual(result[0][1], bytes.fromhex(src[0][1]))
        self.assertEqual(result[1][1], bytes.fromhex(src[1][1]))

    def test_missing_target_beyond_last_remains_unresolved(self):
        src = make((10, b'\xec900\x0e00000\r'), (100, b'\xf5"OK"\r'))
        result, changes = line_targets.resolve_missing_targets(src, Keys, None)
        self.assertEqual(changes, [])
        self.assertEqual(result[0][1], bytes.fromhex(src[0][1]))

    def test_in_line_two_jumps_and_exact_target(self):
        src = make((10, b'\xed70\x0e00000:\xec105\x0e00000\r'),
                   (100, b'\xc9\r'), (110, b'\xf5"END"\r'))
        result, changes = line_targets.resolve_missing_targets(src, Keys, None)
        self.assertEqual(changes, [(10, 70, 100), (10, 105, 110)])
        self.assertIn(b'\xed100\x0e12345:\xec110\x0e12345', result[0][1])

    def test_missing_target_with_spaces_before_colon(self):
        src = make((10, b'\xed70\x0e00000  :\xec105\x0e00000 \r'),
                   (100, b'\xc9\r'), (110, b'\xf5"END"\r'))
        result, changes = line_targets.resolve_missing_targets(src, Keys, None)
        self.assertEqual(changes, [(10, 70, 100), (10, 105, 110)])
        self.assertEqual(result[0][1],
                         b'\xed100\x0e12345  :\xec110\x0e12345 \r')


if __name__ == '__main__':
    unittest.main()
