"""Token bytes must be created only by upstream BAS2TAP, not pyhsb."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import encode_strict_listing
from bas2tap import encode_program


class StrictKeywords(unittest.TestCase):
    def test_print_position_keyword(self):
        p = encode_strict_listing('10 PRINT AT 2,0;"HI"')
        self.assertIn(b'\xac', p)
        self.assertEqual(p, encode_program('10 PRINT AT 2,0;"HI"'))

    def test_no_user_source_rewriting(self):
        for line in ('10 IF DPOR LEN A$>2THEN LET FL=1',
                     '10 PRINT "AT PRINT THEN"',
                     '10 LET AT=123'):
            with self.subTest(line=line):
                try:
                    produced = encode_strict_listing(line)
                except ValueError:
                    with self.assertRaises((ValueError,)):
                        encode_program(line)
                else:
                    self.assertEqual(produced, encode_program(line))
