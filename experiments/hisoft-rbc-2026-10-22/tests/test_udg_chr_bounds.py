import unittest
import sys
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from udg_chr_bounds import allow_bounded_chr_glyphs

@dataclass
class Finding:
    line: int
    operation: str
    severity: str
    classification: str
    expression: str

def probe(source, number, expr):
    rows=[]
    for line in source.splitlines():
        x,y=line.split(' ',1)
        rows.append((int(x),y.encode('ascii')+b'\r'))
    f=Finding(number,'POKE','block','unbounded_memory_write',expr)
    nested=Finding(number,'USR','block','raw_machine_code_address',expr[3:].strip())
    n=allow_bounded_chr_glyphs(rows,{},[f,nested])
    return n, f.severity, nested.severity

class ChrGlyphs(unittest.TestCase):
    def test_complete_single_line_nested_loops(self):
        src='560 FOR x=1TO 8:FOR y=0TO 7:READ a:POKE USR CHR$ (144+x)+y,a:NEXT y:NEXT x'
        self.assertEqual(probe(src,560,'USR CHR$ (144+x)+y,a'),(1,'info','info'))

    def test_spanning_three_lines(self):
        src=('60 FOR K=1TO 7:FOR L=0TO 7:FOR M=1TO 9\n'
             '70 POKE USR CHR$ (143+M)+L,A(K,L*9+M)\n75 NEXT M:NEXT L')
        self.assertEqual(probe(src,70,'USR CHR$ (143+M)+L,A(K,L*9+M)'),(1,'info','info'))

    def test_unrelated_earlier_branch_does_not_invalidate_loop(self):
        src=('500 GO TO 1000\n550 RETURN\n555 POKE USR "a",0\n'
             '560 FOR x=1TO 8:FOR y=0TO 7:READ a:POKE USR CHR$ (144+x)+y,a:NEXT y:NEXT x')
        self.assertEqual(probe(src,560,'USR CHR$ (144+x)+y,a'),(1,'info','info'))

    def test_outside_udg_and_broken_bounds(self):
        for src,expr in [
          ('50 FOR x=1TO 25:FOR y=0TO 7:POKE USR CHR$ (143+x)+y,a:NEXT y:NEXT x','USR CHR$ (143+x)+y,a'),
          ('50 FOR x=1TO 9:FOR y=0TO 8:POKE USR CHR$ (143+x)+y,a:NEXT y:NEXT x','USR CHR$ (143+x)+y,a'),
          ('50 FOR x=1TO 9:FOR y=0TO 7:POKE USR CHR$ (143+x)+y,a','USR CHR$ (143+x)+y,a'),
          ('50 FOR x=1TO 9:FOR y=0TO 7:LET x=255:POKE USR CHR$ (143+x)+y,a:NEXT y:NEXT x','USR CHR$ (143+x)+y,a'),
          ('50 FOR x=1TO 9:FOR y=0TO 7:POKE 23658,255:NEXT y:NEXT x','23658,255')]:
            with self.subTest(src=src):
                self.assertEqual(probe(src,50,expr)[0],0)

    def test_external_jump_to_body_blocks(self):
        src=('10 GO TO 70\n60 FOR M=1TO 9:FOR L=0TO 7\n'
             '70 POKE USR CHR$ (143+M)+L,a\n80 NEXT L:NEXT M')
        self.assertEqual(probe(src,70,'USR CHR$ (143+M)+L,a')[0],0)

if __name__=='__main__': unittest.main()