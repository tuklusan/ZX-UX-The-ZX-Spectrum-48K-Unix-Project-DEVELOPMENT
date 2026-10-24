"""Do not guess where missing Sinclair BASIC keywords begin."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from basic_listing import split_numbered_line, tokenize_preserving_numeric_at

class StubSource:
    @staticmethod
    def tokenize_line(body, kw):
        return body.encode('ascii')

class StrictInput(unittest.TestCase):
    def test_numbered(self):
        self.assertEqual(split_numbered_line('10 FOR I=1 TO 10'),(10,'FOR I=1 TO 10'))
    def test_no_spaces_repaired(self):
        self.assertEqual(tokenize_preserving_numeric_at('FOR I=1TO10',StubSource,None),
                         b'FOR I=1TO10')
    def test_surrounding_spaces_retained(self):
        self.assertEqual(split_numbered_line('10 PRINT  9  '),(10,'PRINT  9  '))
    def test_non_ascii_rejected(self):
        with self.assertRaisesRegex(ValueError,'non-ASCII'):
            tokenize_preserving_numeric_at('LET a=↑',StubSource,None)
    def test_invalid_lines(self):
        for text in ('', '10000 PRINT 1','PRINT 1'):
            with self.subTest(text=text),self.assertRaises(ValueError):
                split_numbered_line(text)

if __name__=='__main__':unittest.main()