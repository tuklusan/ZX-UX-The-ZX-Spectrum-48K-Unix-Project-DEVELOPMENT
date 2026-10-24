"""Regression checks for the blanket executable Sinclair USR-token ban."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from safety_usr import UnsupportedUsr, enforce_numeric_usr


def tokens(line):
    return line.replace(b'{USR}', bytes((0xc0,))).replace(b'{REM}', bytes((0xea,)))


class UsrTokenSafetyTests(unittest.TestCase):
    def test_numeric_usr_rejected_in_any_expression(self):
        forms = (b'PRINT {USR} 32768', b'LET A={USR} 3280',
                 b'GO TO {USR} 32768', b'IF {USR} 7 THEN RUN',
                 b'DATA {USR} 3280:READ A')
        for form in forms:
            with self.subTest(form=form), self.assertRaisesRegex(UnsupportedUsr, 'E_USR_TOKEN: Line 20'):
                enforce_numeric_usr([(20, tokens(form))], [])

    def test_graphics_usr_is_also_rejected(self):
        for form in (b'POKE {USR} "a",255', b'POKE {USR} CHR$ (144+X),7',
                     b'LET X={USR} "b"'):
            with self.subTest(form=form), self.assertRaisesRegex(UnsupportedUsr, 'USR token 0xC0'):
                enforce_numeric_usr([(42, tokens(form))], [])

    def test_nonexecuting_bytes_do_not_trigger(self):
        lines = [(10, tokens(b'PRINT "{USR}"')),
                 (20, tokens(b'{REM} {USR} 3280')),
                 (30, tokens(b'PRINT "USR 32768"')),
                 (40, tokens(b'PRINT "TEXT":{REM} {USR}'))]
        enforce_numeric_usr(lines, [])

    def test_numeric_cache_cannot_impersonate_usr(self):
        enforce_numeric_usr([(10, b'PRINT 1\x0e\xc0\x00\x00\x00\x00')], [])

    def test_invalid_numeric_cache_fails_closed(self):
        with self.assertRaisesRegex(UnsupportedUsr, 'Truncated'):
            enforce_numeric_usr([(10, b'PRINT 1\x0e\xc0')], [])

    def test_code_after_data_and_colon_is_detected(self):
        with self.assertRaisesRegex(UnsupportedUsr, 'Line 60'):
            enforce_numeric_usr([(60, tokens(b'DATA 42:LET A={USR} 123'))], [])


if __name__ == '__main__':
    unittest.main()
