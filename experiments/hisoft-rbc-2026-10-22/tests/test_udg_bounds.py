"""Bounded graphics initialization must never open general memory writes."""
import sys
import unittest
from pathlib import Path
from dataclasses import dataclass
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))

@dataclass
class Finding:
    line: int
    operation: str
    severity: str
    classification: str
    expression: str

from udg_bounds import allow_bounded_udg_loops


def check(src, line, expr):
    rows = [(int(t.split(' ', 1)[0]), t.split(' ', 1)[1].encode()+b'\r')
            for t in src.strip().split('\n')]
    f = Finding(line, 'POKE', 'block', 'unbounded_memory_write', expr)
    changed=allow_bounded_udg_loops(rows, {}, [f])
    return changed, f.severity


class UDGLoops(unittest.TestCase):
    def test_nearby_single_glyph(self):
        lines='3005 FOR i=0 TO 7:READ gr\n3010 POKE USR "a"+i,gr\n3020 NEXT i'
        self.assertEqual(check(lines,3010,'USR "a"+i,gr'),(1,'info'))

    def test_pointer_loop_and_glyph_upper_bound(self):
        source='6000 FOR x=USR "a" TO USR "a"+87\n6010 READ n:POKE x,n\n6020 NEXT x'
        self.assertEqual(check(source,6010,'x,n'),(1,'info'))
        invalid=source.replace('+87','+168')
        self.assertEqual(check(invalid,6010,'x,n'),(0,'block'))

    def test_other_index_is_not_approved(self):
        source='6000 FOR x=USR "a" TO USR "g"+7\n6010 POKE z,n\n6020 NEXT x'
        self.assertEqual(check(source,6010,'z,n'),(0,'block'))

    def test_direct_jump_inside_loop_blocks_approval(self):
        source='10 GO TO 6010\n6000 FOR x=USR "a" TO USR "a"+7\n6010 POKE x,n\n6020 NEXT x'
        self.assertEqual(check(source,6010,'x,n'),(0,'block'))

    def test_conditional_in_body_blocks_approval(self):
        source='6000 FOR x=USR "a" TO USR "a"+7\n6010 IF n THEN POKE x,n\n6020 NEXT x'
        self.assertEqual(check(source,6010,'x,n'),(0,'block'))

    def test_literal_system_address_stays_blocked(self):
        source='6000 FOR x=USR "a" TO USR "a"+7\n6010 POKE 23658,n\n6020 NEXT x'
        self.assertEqual(check(source,6010,'23658,n'),(0,'block'))

    def test_char_pointer_with_parentheses(self):
        source='9040 FOR F=0 TO 7:READ A,B\n9050 POKE USR ("A")+F,A\n9060 POKE USR ("B")+F,128\n9070 POKE USR ("C")+F,B\n9080 NEXT F'
        self.assertEqual(check(source,9050,'USR ("A")+F,A'),(1,'info'))
        self.assertEqual(check(source,9060,'USR ("B")+F,128'),(1,'info'))
        self.assertEqual(check(source,9070,'USR ("C")+F,B'),(1,'info'))

    def test_other_io_stays_blocked(self):
        src='7000 FOR i=0 TO 7\n7010 POKE 60000+i,7\n7020 NEXT i'
        self.assertEqual(check(src,7010,'60000+i,7'),(0,'block'))

if __name__ == '__main__':
    unittest.main()