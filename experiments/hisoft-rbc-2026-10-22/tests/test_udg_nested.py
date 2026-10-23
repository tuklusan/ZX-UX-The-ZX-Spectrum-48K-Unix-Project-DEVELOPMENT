"""Prove nested-loop custom glyph memory writes without allowing raw POKEs."""
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
# test installation imports the independent visible token decoder
from udg_nested import allow_nested_glyph_writes

@dataclass
class Finding:
    line:int
    operation:str='POKE'
    severity:str='block'
    classification:str='unbounded_memory_write'
    expression:str='USR "{90}"+y,t'


def check(lines, item):
    rows=[(int(s.split(' ',1)[0]),s.split(' ',1)[1].encode()+b'\r') for s in lines.split('\n')]
    return allow_nested_glyph_writes(rows,{},[item]),item.severity

class NestedTests(unittest.TestCase):
    def test_original_flying_bomb_outer_loop(self):
        src=('8999 STOP\n9000 FOR y=0TO 7:INPUT a$:LET t=0:FOR x=1TO 8:LET t=t+2^(8-x)*VAL a$(x):NEXT x:PRINT t\n'
             '9010 POKE USR "{90}"+y,t\n9020 NEXT x:NEXT y')
        self.assertEqual(check(src,Finding(9010)),(1,'info'))

    def test_outside_loop(self):
        self.assertEqual(check('9000 POKE USR "{90}"+y,t',Finding(9000)),(0,'block'))

    def test_outside_udg(self):
        src='9000 FOR y=0TO 7\n9010 POKE 23658+y,1\n9020 NEXT y'
        self.assertEqual(check(src,Finding(9010,expression='23658+y,1')),(0,'block'))
        self.assertEqual(check(src,Finding(9010,expression='USR "{A5}"+y,1')),(0,'block'))

    def test_outer_variable_change_blocked(self):
        s='9000 FOR y=0TO 7\n9005 LET y=100\n9010 POKE USR "{90}"+y,t\n9020 NEXT y'
        self.assertEqual(check(s,Finding(9010)),(0,'block'))

    def test_external_entry_blocked(self):
        s='10 GO TO 9010\n9000 FOR y=0TO 7\n9010 POKE USR "{90}"+y,t\n9020 NEXT y'
        self.assertEqual(check(s,Finding(9010)),(0,'block'))

    def test_read_index_blocked(self):
        s='9000 FOR y=0TO 7\n9005 READ y\n9010 POKE USR "{90}"+y,t\n9020 NEXT y'
        self.assertEqual(check(s,Finding(9010)),(0,'block'))

if __name__ == '__main__':unittest.main()