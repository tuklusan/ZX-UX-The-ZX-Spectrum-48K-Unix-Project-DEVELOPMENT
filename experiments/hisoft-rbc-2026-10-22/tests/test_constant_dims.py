import sys,re,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from constant_dims import specialize_literal_dims

class Kw: TOKEN={0xf1:'LET',0xe9:'DIM',0xf2:'GO TO',0xed:'GO SUB'}
class Source:
 def hide_numbers(self,b,fp):return b+b'\x0e'+bytes(5)
class Tap:
 def split_lines(self,p):return p
 def join_lines(self,p):return p

def convert(p):
 rows=[]
 for n,s in p:
  b=s.encode()
  for token,name in Kw.TOKEN.items(): b=re.sub(rb'\b'+name.encode()+rb'\b',bytes((token,)),b)
  rows.append((n,b+b'\r'))
 return specialize_literal_dims(rows,Kw(),None,Source(),Tap())

class Dims(unittest.TestCase):
 def test_constant_immediately_before_many_dims(self):
  changed,proof=convert([(3390,'LET x=10'),(3400,'DIM a(x):DIM b(x):DIM c(x)')])
  self.assertEqual(len(proof),1)
  self.assertEqual(proof[0]['arrays'],3)
  self.assertEqual(changed[1][1].count(b'\x0e'),3)
 def test_external_jump_rejects(self):
  self.assertFalse(convert([(20,'GO TO 3400'),(3390,'LET x=10'),(3400,'DIM a(x)')])[1])
 def test_computed_jump_rejects(self):
  self.assertFalse(convert([(20,'GO TO target'),(3390,'LET x=10'),(3400,'DIM a(x)')])[1])
 def test_jump_to_missing_intermediate_line_rejects(self):
  self.assertFalse(convert([(20,'GO TO 3395'),(3390,'LET x=10'),(3400,'DIM a(x)')])[1])
 def test_intervening_literal_unchanged_variable(self):
  updated,proof=convert([(3390,'LET x=10'),(3400,'DIM a(x)'),
                         (3500,'DIM i(3)'),(3510,'LET w$="hello"'),
                         (3520,'DIM j(x):DIM l(x)')])
  self.assertEqual([p['dim_line'] for p in proof],[3400,3520])
 def test_intervening_mutation_blocks(self):
  rows=[(3390,'LET x=10'),(3400,'DIM a(x)'),(3510,'LET x=11'),(3520,'DIM j(x)')]
  updated,proof=convert(rows)
  self.assertEqual([p['initializer_line'] for p in proof],[3390,3510])
 def test_intervening_expression_blocks(self):
  rows=[(3390,'LET x=10'),(3500,'LET y=z+1'),(3520,'DIM j(x)')]
  self.assertFalse(convert(rows)[1])

 def test_original_asset_stripper_tape(self):
  import hashlib
  source=(Path(__file__).resolve().parents[3] / 'src/bonus/60-programs/'
          '41-asset-stripper/BASIC/41-asset-stripper.tzx')
  if not source.exists():self.skipTest('Original tape not mounted in test checkout')
  image=source.read_bytes()
  self.assertEqual(hashlib.sha1(('blob '+str(len(image))+'\0').encode()+image).hexdigest(),
                   'bcd90b2bff5f193a98dc21fe607d32c97f2f568e')
  self.assertTrue(image.startswith(b'ZXTape!\x1a'))
  cursor=10;blocks=[]
  while cursor<len(image):
   self.assertEqual(image[cursor],16)
   size=int.from_bytes(image[cursor+3:cursor+5],'little')
   cursor+=5;blocks.append(image[cursor:cursor+size]);cursor+=size
  data=blocks[1][1:-1];cursor=0;rows=[]
  while cursor<len(data):
   line=int.from_bytes(data[cursor:cursor+2],'big')
   size=int.from_bytes(data[cursor+2:cursor+4],'little')
   cursor+=4;rows.append((line,data[cursor:cursor+size]));cursor+=size
  updated,proof=specialize_literal_dims(rows,Kw(),None,Source(),Tap())
  self.assertEqual(len(proof),2)
  self.assertEqual([p['arrays'] for p in proof],[10,2])
  self.assertEqual([n for n,b in updated if b!=dict(rows)[n]],[3400,3520])

 def test_computed_initializer_rejects(self):
  self.assertFalse(convert([(3390,'LET x=10+a'),(3400,'DIM a(x)')])[1])
 def test_wrong_variable_rejects(self):
  self.assertFalse(convert([(3390,'LET x=10'),(3400,'DIM a(y)')])[1])
 def test_unrelated_statements_reject(self):
  self.assertFalse(convert([(3390,'LET x=10'),(3400,'DIM a(x):PRINT 3')])[1])
 def test_true_dynamic_input_reject(self):
  self.assertFalse(convert([(30,'INPUT a'),(40,'DIM p(a)')])[1])
if __name__=='__main__':unittest.main()