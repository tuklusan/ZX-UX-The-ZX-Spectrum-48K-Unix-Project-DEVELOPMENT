"""Check text keyword boundaries against known original BASIC lines."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import normalize_listing, split_numbered_line


class ListingBoundaries(unittest.TestCase):
    def test_galaxians_if_then(self):
        self.assertIn('hs THEN ', normalize_listing('IF sc>hsTHEN LET hs=sc'))
        self.assertIn('c$ THEN ', normalize_listing('IF a$=c$THEN GO TO 2000'))

    def test_invaders_for_to_and_if_then(self):
        line='FOR X=UTO P:IF I(X+L*P)=UTHEN NEXT X'
        result=normalize_listing(line)
        self.assertIn('=U TO  P', result)
        self.assertIn('=U THEN  NEXT', result)

    def test_strings_and_rem_not_rewritten(self):
        line='PRINT "IF aTHEN FOR X=UTO P":REM IF aTHEN FOR X=UTO P'
        self.assertEqual(normalize_listing(line), line)

    def test_preserve_variable_substrings(self):
        line='LET AFTER=1:LET TOTAL=2:PRINT "METHOD"'
        self.assertEqual(normalize_listing(line), line)

    def test_power_glyph_in_expression_and_literal(self):
        self.assertEqual(normalize_listing('LET x=2↑(INT (RND *6))'),
                         'LET x=2^(INT (RND *6))')
        self.assertEqual(normalize_listing('PRINT "↑":REM ↑'),
                         'PRINT "^":REM ^')

    def test_original_source_text_unchanged(self):
        original = 'LET z=3↑2'
        self.assertEqual(normalize_listing(original), 'LET z=3^2')
        self.assertEqual(original, 'LET z=3↑2')


    def test_numbered_empty_basic_line(self):
        self.assertEqual(split_numbered_line('8 '), (8, ' '))
        self.assertEqual(split_numbered_line('8'), (8, ' '))
        self.assertEqual(split_numbered_line('  8  '), (8, ' '))

    def test_numbered_program_statement(self):
        self.assertEqual(split_numbered_line('10 GO SUB 70'), (10, 'GO SUB 70'))
        self.assertEqual(split_numbered_line('0 REM : OPEN #'), (0, 'REM : OPEN #'))

    def test_preserved_mushroom_line_matches_tape(self):
        root = Path(__file__).resolve().parents[3]
        folder = root / 'src/bonus/60-programs/59-mushroom-invasion/BASIC'
        listing = folder / '59-mushroom-invasion.bas'
        tape = folder / '59-mushroom-invasion.tzx'
        if not listing.is_file() or not tape.is_file():
            self.skipTest('read-only game sources not present in isolated test tree')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from corpus_line_audit import basic_lines
        raw = listing.read_text(encoding='utf-8-sig').splitlines()[2]
        number, body = split_numbered_line(raw)
        self.assertEqual(number, 8)
        self.assertEqual(body.encode('latin-1') + b'\r', basic_lines(tape.read_bytes())[8])

    def test_numbered_line_rejects_invalid_text(self):
        for raw in ('PRINT HELLO', '10000 PRINT HELLO', ''):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                split_numbered_line(raw)


if __name__ == '__main__':
    unittest.main()
