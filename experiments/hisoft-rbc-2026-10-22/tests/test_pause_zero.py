"""Sinclair PAUSE 0 transformation tests for the temporary compiler copy."""
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from pause_zero import rewrite_pause_zero


class Keywords:
    CODE_FOR = {'PAUSE': 0xf2, 'REM': 0xea}


def run(rows):
    fake_tap = types.ModuleType('tap')
    fake_tap.split_lines = lambda data: list(data)
    fake_tap.join_lines = lambda data: list(data)
    fake_source = types.ModuleType('source')
    fake_source.tokenize_line = lambda text, kw: text.encode('ascii')
    fake_source.hide_numbers = lambda body, fp: body
    with patch.dict(sys.modules, {'tap': fake_tap, 'source': fake_source}):
        return rewrite_pause_zero(rows, Keywords, None)


class PauseZeroTests(unittest.TestCase):
    def test_galaxians_wait_and_return(self):
        before = [(8050, b'\xf2' + b'0\x0e\x00\x00\x00\x00\x00:\xfb:\xfe\r'),
                  (9000, b'NEXT\r')]
        saved = list(before)
        rewritten, changes = run(before)
        self.assertEqual(before, saved)
        self.assertEqual(changes, [(8050, 8050, 8051)])
        self.assertEqual([n for n, _ in rewritten], [8050, 8051, 9000])
        self.assertEqual(rewritten[0][1], b'IF INKEY$="" THEN GO TO 8050\r')
        self.assertEqual(rewritten[1][1], b'\xfb:\xfe\r')

    def test_bare_wait(self):
        rewritten, changes = run([(10, b' \xf2 0\r'), (20, b'NEXT\r')])
        self.assertEqual(changes, [(10, 10, None)])
        self.assertEqual(rewritten[0][1], b'IF INKEY$="" THEN GO TO 10\r')
        self.assertEqual(len(rewritten), 2)

    def test_no_free_line_fails_closed(self):
        original = [(100, b'\xf2' + b'0\x0e12345:\xfb\r'),
                    (101, b'NEXT\r')]
        self.assertEqual(run(original), (original, []))

    def test_unconditional_inline_pause_uses_two_free_lines(self):
        original = [(120, b'\xf5"START":\xf20\x0e12345:\xfb:\xfe\r'),
                    (150, b'NEXT\r')]
        rewritten, changes = run(original)
        self.assertEqual(changes, [(120, 121, 122)])
        self.assertEqual(rewritten, [
            (120, b'\xf5"START"\r'),
            (121, b'IF INKEY$="" THEN GO TO 121\r'),
            (122, b'\xfb:\xfe\r'),
            (150, b'NEXT\r'),
        ])

    def test_nested_conditional_pause_is_not_moved(self):
        original = [(100, b'\xfaX=1\xcb\xf5"Y":\xf20\x0e12345:\xfb\r'),
                    (200, b'NEXT\r')]
        self.assertEqual(run(original), (original, []))

    def test_two_consecutive_waits(self):
        original = [(300, b'\xf20\x0e12345:\xf20\x0e12345:\xfb\r'),
                    (400, b'NEXT\r')]
        rewritten, changes = run(original)
        self.assertEqual(changes, [(300, 300, 301), (301, 301, 302)])
        self.assertEqual([n for n, _ in rewritten], [300, 301, 302, 400])
        self.assertEqual(rewritten[2][1], b'\xfb\r')

    def test_quoted_text_does_not_create_false_wait(self):
        original = [(100, b'\xf5"PAUSE 0:HI":\xf20\x0e12345:\xfb\r'),
                    (200, b'NEXT\r')]
        rewritten, changes = run(original)
        self.assertEqual(changes, [(100, 101, 102)])
        self.assertEqual(rewritten[0][1], b'\xf5"PAUSE 0:HI"\r')

    def test_nonzero_and_computed_waits_are_untouched(self):
        original = [(10, b'\xf2' + b'10\x0e12345\r'),
                    (20, b'\xf2' + b'0\x0e12345+N\r'),
                    (30, b'\xf5"PAUSE 0"\r')]
        self.assertEqual(run(original), (original, []))

    def test_archived_galaxians_has_expected_unmodified_line(self):
        root = Path(__file__).resolve().parents[3]
        source = (root / 'src/bonus/60-programs/25-galaxians/BASIC/'
                  '25-galaxians.bas')
        if not source.is_file():
            self.skipTest('original BASIC source not installed here')
        rows = [line for line in source.read_text(encoding='latin-1').splitlines()
                if line.startswith('8050 ')]
        self.assertEqual(len(rows), 1)
        self.assertRegex(rows[0], r'^8050 PAUSE 0:CLS ?:\s*RETURN$')



if __name__ == '__main__':
    unittest.main()
