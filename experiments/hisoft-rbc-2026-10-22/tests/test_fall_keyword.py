"""The strict input adapter never corrects old missing keyword boundaries."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import tokenize_preserving_numeric_at

class LiteralTokenizer:
    @staticmethod
    def tokenize_line(body, kw):
        return body.encode('ascii')

class OriginalText(unittest.TestCase):
    def test_fall_guy_joined_operators_remain(self):
        original='CLS :LET w$=(b$AND f=21)+(c$AND f1=21):IF f=21AND f1=21THEN GO TO 5050'
        self.assertEqual(tokenize_preserving_numeric_at(original,LiteralTokenizer,None),
                         original.encode('ascii'))

    def test_unspaced_for_kept_verbatim(self):
        original='FOR J=11TO 1STEP -1'
        self.assertEqual(tokenize_preserving_numeric_at(original,LiteralTokenizer,None),
                         original.encode('ascii'))

    def test_strings_and_identifiers(self):
        for text in ('LET COMMAND=1','LET BAND=3','PRINT "b$AND x=1"','REM b$AND x=1'):
            self.assertEqual(tokenize_preserving_numeric_at(text,LiteralTokenizer,None),
                             text.encode('ascii'))

if __name__=='__main__':
    unittest.main()