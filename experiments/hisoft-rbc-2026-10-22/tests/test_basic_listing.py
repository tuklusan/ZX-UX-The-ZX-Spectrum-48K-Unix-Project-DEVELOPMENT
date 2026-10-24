"""RBC uses the vendored upstream encoder as its only external tokenizer."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import encode_strict_listing, split_numbered_line, UPSTREAM_REVISION
from bas2tap import encode_program, BAS2TAPError


class StrictInput(unittest.TestCase):
    def test_revision_and_exact_upstream_output(self):
        self.assertEqual(UPSTREAM_REVISION, '0ddb25e4c38ce4ccb5a43e85fb57e683bd274f59')
        for listing in ('10 PRINT "HELLO"\n20 PRINT 2',
                        '10 FOR I=1 TO 10: NEXT I',
                        '10 REM PRINT: THEN  44',
                        '10 PRINT "{A}{90}{INK 3}"',
                        '10 DEF FN A(X,Y)=X+Y',
                        '10 PRINT 2.5E-3'):
            with self.subTest(listing=listing):
                self.assertEqual(encode_strict_listing(listing),
                                 encode_program(listing, syntax_check=False))

    def test_numbered_ascii_input(self):
        self.assertEqual(split_numbered_line('10 PRINT  9  '), (10,'PRINT  9  '))
        self.assertEqual(split_numbered_line('114: FOR I=1 TO 40'), (114, ': FOR I=1 TO 40'))
        self.assertEqual(encode_strict_listing('114: FOR I=1 TO 40'),
                         encode_program('114: FOR I=1 TO 40'))
        for line in ('', '10000 PRINT 1', 'PRINT 1', '10PRINT 1'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                split_numbered_line(line)

    def test_for_numeric_keyword_boundary_is_not_invented(self):
        with self.assertRaisesRegex(ValueError, 'missing whitespace before TO'):
            encode_strict_listing('10 FOR I=1TO10')
        self.assertTrue(encode_strict_listing('10 FOR I=1 TO 10'))
        self.assertTrue(encode_strict_listing('10 PRINT "FOR I=1TO10"'))
        self.assertTrue(encode_strict_listing('10 REM FOR I=1TO10'))
        self.assertTrue(encode_strict_listing('10 DATA "FOR I=1TO10": PRINT 5'))

    def test_grammar_disambiguates_at_variable_and_position_control(self):
        from bas2tap_syntax import check_program
        from bas2tap import tokenize_line
        samples = {
            'LET AT=0': b'\xf1AT=',
            'IF AT=1 THEN LET AT=2': b'\xfaAT=',
            'LET A$=STR$ (AT)': b'(AT)',
            'READ AT,A$': b'\xe3AT,A$',
            'DIM AT(4)': b'\xe9AT(',
            'PRINT AT 2,0': b'\xf5\xac',
            'INPUT AT 2,0;AT': b'\xee\xac',
            'LPRINT AT 2,0': b'\xe0\xac',
            'PRINT AT;': b'\xf5AT;',
            'PRINT AT,1': b'\xf5AT,',
        }
        for body, required in samples.items():
            with self.subTest(body=body):
                data = tokenize_line(body)
                self.assertIn(required, data)
                listing = encode_strict_listing('10 ' + body)
                self.assertEqual(listing[4:], data)
                check_program(listing)
        for body in ('FOR AT=1 TO 2', 'NEXT AT', 'LET AT$="X"'):
            with self.subTest(body=body), self.assertRaises(Exception):
                check_program(encode_strict_listing('10 ' + body))

    def test_escaped_large_line_uses_upstream_lexer(self):
        long_source = '10 PRINT "' + ('AB' * 550) + '"'
        self.assertGreater(len(encode_strict_listing(long_source)), 1000)

    def test_non_ascii_duplicates_and_missing_line(self):
        for source in ('10 PRINT "£"', '10 PRINT 1\n10 PRINT 2',
                       '20 PRINT 1\n10 PRINT 2', 'PRINT 2', '', '\n\n'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                encode_strict_listing(source)

    def test_original_c_tokenized_numeric_bytes(self):
        program = encode_strict_listing('10 PRINT 10')
        self.assertIn(b'10\x0e\x00\x00\x0a\x00\x00', program)

    def test_nonexecuted_quote_and_rem(self):
        encoded = encode_strict_listing('10 PRINT "USR 0"\n20 REM VAL "USR 0"')
        self.assertIn(b'"USR 0"', encoded)
        self.assertIn(b'VAL "USR 0"', encoded)