import sys,re,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from duplicate_for import remove_duplicate_for
class T:
 def split_lines(self,p): return p
 def join_lines(self,p): return p
class K: TOKEN={0xeb:'FOR',0xcc:'TO',0xea:'REM',0xf3:'NEXT'}

def convert(lines):
 out=[]
 for n,txt in lines:
  b=txt.encode()
  for code,name in K.TOKEN.items():b=re.sub(rb'\b'+name.encode()+rb'\b',bytes((code,)),b)
  out.append((n,b+b'\r'))
 return remove_duplicate_for(out,K(),T())

class ForTests(unittest.TestCase):
 def test_matching_literal_for(self):
  new,proof=convert([(3690,'FOR x=1TO 10'),(3699,'FOR x=1TO 10'),(3700,'LET a(x)=3'),(3780,'NEXT x')])
  self.assertEqual(proof,[(3690,3699,'x')]);self.assertEqual(new[0][1],b'\xea\r')
 def test_different_variable_rejected(self):
  self.assertFalse(convert([(1,'FOR x=1TO 10'),(2,'FOR y=1TO 10')])[1])
 def test_different_bound_rejected(self):
  self.assertFalse(convert([(1,'FOR x=1TO 10'),(2,'FOR x=1TO 11')])[1])
 def test_work_between_rejected(self):
  self.assertFalse(convert([(1,'FOR x=1TO 10'),(2,'LET y=10'),(3,'FOR x=1TO 10')])[1])
 def test_side_effect_bound_rejected(self):
  self.assertFalse(convert([(1,'FOR x=1TO n'),(2,'FOR x=1TO n')])[1])
 def test_step_rejected(self):
  self.assertFalse(convert([(1,'FOR x=1TO 10STEP 2'),(2,'FOR x=1TO 10STEP 2')])[1])
if __name__=='__main__':unittest.main()