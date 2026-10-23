"""Check text keyword boundaries against known original BASIC lines."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import normalize_listing


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


if __name__ == '__main__':
    unittest.main()
