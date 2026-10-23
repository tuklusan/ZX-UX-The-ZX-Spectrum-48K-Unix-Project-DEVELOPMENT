"""Check that direct machine-code USR is never granted an exception."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage'))
from audit_policy import audit_lines, from_text, lines_from_tzx
from safety_usr import UnsupportedUsr, enforce_numeric_usr


class Finding:
    def __init__(self, line, classification, severity='block'):
        self.line = line
        self.operation = 'USR'
        self.classification = classification
        self.severity = severity


def tokens(line):
    # Real Spectrum USR token, not the letters in a screen message.
    return line.replace(b'{USR}', bytes((0xc0,)))


class NumericUsrSafetyTests(unittest.TestCase):
    def test_rom_scroll_exception_is_still_rejected(self):
        # The previous memory helper had admitted this machine-code call.
        row = tokens(b'LET I={USR} 3280')
        with self.assertRaisesRegex(UnsupportedUsr, r'E_MACHINE_CODE: Line 7080'):
            enforce_numeric_usr([(7080, row)], [Finding(7080, 'rom_screen_scroll', 'info')])

    def test_numeric_expression_contexts_fail(self):
        contexts=(b'PRINT {USR} 32768',b'LET A={USR} 32768',
                  b'IF {USR} 32768=1 THEN PRINT 1', b'GO TO {USR} (32768)',
                  b'RANDOMIZE {USR} 32768')
        for body in contexts:
            with self.subTest(body=body):
                with self.assertRaisesRegex(UnsupportedUsr, 'Direct execution'):
                    enforce_numeric_usr([(150,tokens(body))],[Finding(150,'raw_machine_code_address')])

    def test_nonexecuting_string_literal_passes(self):
        enforce_numeric_usr([(10,tokens(b'POKE {USR} "a",255'))],
                            [Finding(10,'process_udg_pointer','info')])

    def test_approved_computed_string_requires_matching_review(self):
        code=tokens(b'POKE {USR} CHR$ (144+K)+J,255')
        enforce_numeric_usr([(100,code)], [Finding(100,'process_udg_pointer','info')])
        with self.assertRaisesRegex(UnsupportedUsr,'Cannot prove USR'):
            enforce_numeric_usr([(100,code)], [Finding(100,'raw_machine_code_address')])

    def test_quoted_rem_and_data_are_ignored(self):
        code=tokens(b'PRINT "USR 3280":REM {USR} 3280')
        enforce_numeric_usr([(10,code)],[])
        code=tokens(b'DATA {USR} 32768:PRINT 9')
        enforce_numeric_usr([(11,code)],[])

    def test_original_hangman_both_input_forms(self):
        folder = Path(__file__).resolve().parents[3] / 'src/bonus/60-programs/55-hangman/BASIC'
        bas = audit_lines(from_text((folder/'55-hangman.bas').read_bytes()), 'text')
        tape = lines_from_tzx((folder/'55-hangman.tzx').read_bytes())
        tzx = audit_lines(tape, 'tape')
        for records in (bas, tzx):
            hit = [(x['line'], x['status']) for x in records
                   if x['operation'] == 'USR']
            self.assertEqual(hit, [(7080, 'numeric_usr')])
        with self.assertRaisesRegex(UnsupportedUsr, r'E_MACHINE_CODE: Line 7080'):
            enforce_numeric_usr(tape, [Finding(7080, 'rom_screen_scroll', 'info')])

    def test_reject_bad_review_alignment(self):
        with self.assertRaisesRegex(UnsupportedUsr,'Unmatched USR'):
            enforce_numeric_usr([(10,b'PRINT "Hello"')], [Finding(10,'raw_machine_code_address')])


if __name__ == '__main__':
    unittest.main()
