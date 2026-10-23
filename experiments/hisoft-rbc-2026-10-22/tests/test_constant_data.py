"""Literal DATA conversion needs complete local proof, or leaves input alone."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from constant_data import adapt_literal_data

class Tap:
    def split_lines(self,program):return program
    def join_lines(self,rows):return rows
class Kw:
    TOKEN={0xe5:'RESTORE',0xe4:'DATA',0xf1:'LET',0xeb:'FOR',0xe3:'READ',0xf3:'NEXT'}
class Source:
    def hide_numbers(self,txt,fp):return txt+b'\x0e'+bytes(5)

def test(rows):
    program=[(n,body.encode('latin-1').replace(b'DATA ',bytes([0xe4]))+b'\r') for n,body in rows]
    revised,proofs=adapt_literal_data(program,Kw(),None,Source(),Tap())
    return revised,proofs,program

class DataTests(unittest.TestCase):
    def test_small_bounded_music_data(self):
        rows=[(9100,'LET g=.3:RESTORE 9200:FOR f=1TO 2:READ y,x:BEEP y,x:NEXT f:RETURN'),
              (9200,'DATA g,7,g,9')]
        revised,proofs,_=test(rows)
        self.assertEqual(len(proofs),1)
        self.assertEqual(proofs[0]['fields'],4)
        self.assertEqual(revised[1][1].count(b'\x0e'),2)

    def test_missing_initializer_is_unchanged(self):
        rows=[(9100,'RESTORE 9200:FOR f=1TO 2:READ y,x:NEXT f'),
              (9200,'DATA g,7,g,9')]
        result,proofs,original=test(rows)
        self.assertEqual((result,proofs),(original,[]))

    def test_computed_data_not_folded(self):
        rows=[(9100,'LET g=3*x:RESTORE 9200:FOR f=1TO 2:READ y,x:NEXT f'),
              (9200,'DATA g,7,g,9')]
        result,proofs,original=test(rows)
        self.assertEqual((result,proofs),(original,[]))

    def test_other_read_path_prevents_fold(self):
        rows=[(100,'READ x'),(9100,'LET g=.3:RESTORE 9200:FOR f=1TO 2:READ y,x:NEXT f'),
              (9200,'DATA g,7,g,9')]
        result,proofs,original=test(rows)
        self.assertEqual((result,proofs),(original,[]))

    def test_second_write_invalidates_first_initializer(self):
        rows=[(9100,'LET g=.3:LET g=g+1:RESTORE 9200:FOR f=1TO 2:READ y,x:NEXT f'),
              (9200,'DATA g,7,g,9')]
        result,proofs,original=test(rows)
        self.assertEqual((result,proofs),(original,[]))

    def test_nonmatching_data_count_unchanged(self):
        rows=[(9100,'LET g=.3:RESTORE 9200:FOR f=1TO 2:READ y,x:NEXT f'),
              (9200,'DATA g,7,g')]
        result,proofs,original=test(rows)
        self.assertEqual((result,proofs),(original,[]))

    def test_branch_before_read_unchanged(self):
        rows=[(9100,'LET g=.3:RESTORE 9200:IF a THEN GO TO 9200:FOR f=1TO 2:READ y,x:NEXT f'),
              (9200,'DATA g,7,g,9')]
        result,proofs,original=test(rows)
        self.assertEqual((result,proofs),(original,[]))

if __name__=='__main__': unittest.main()