import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from glyph_data import specialize_glyph_data

class Tap:
    def split_lines(self,p): return p
    def join_lines(self,lines): return lines
class Kw:
    TOKEN={0xe5:'RESTORE',0xe4:'DATA',0xf1:'LET',0xeb:'FOR',0xe3:'READ',0xf3:'NEXT',0xf4:'POKE',0xc0:'USR',0xcc:'TO',0xf2:'GO TO',0xf5:'GO SUB',0xea:'REM'}
class Source:
    def hide_numbers(self,b,fp): return b + b'\x0e'+bytes(5)

def probe(lines):
    rows=[]
    for number,text in lines:
        body=text.encode('ascii')
        for tok,name in Kw.TOKEN.items():
            import re
            body=re.sub(rb'\b'+name.encode()+rb'\b',bytes((tok,)),body)
        rows.append((number,body+b'\r'))
    return specialize_glyph_data(rows,Kw(),None,Source(),Tap())

GOOD=[
 (10,'GO SUB 9000'),
 (9000,'RESTORE 9010:LET f=0:LET g=255:FOR y=USR "a"TO USR "b"+7:READ x:POKE y,x:NEXT y'),
 (9010,'DATA f,2,g,4,f,6,7,8'),
 (9020,'DATA 9,10,11,12,g,14,15,16'),
]
class GlyphDataTests(unittest.TestCase):
    def test_bounded_two_glyphs(self):
        rows,p=probe(GOOD)
        self.assertEqual(len(p),1)
        self.assertEqual(p[0]['entries'],16)
        self.assertEqual(rows[2][1].count(b'\x0e'),3)
    def test_preserved_championship_tape(self):
        import hashlib
        path=(Path(__file__).resolve().parents[3] / 'src/bonus/60-programs/'
              '05-championship-boxing/BASIC/05-championship-boxing.tzx')
        if not path.is_file():
            self.skipTest('Original tape not present in this checkout')
        image=path.read_bytes()
        blob=hashlib.sha1(('blob '+str(len(image))+'\0').encode()+image).hexdigest()
        self.assertEqual(blob,'34b44a3a25a0401639f4743db06eaa915c9e2ef9')
        self.assertTrue(image.startswith(b'ZXTape!\x1a'))
        cursor=10
        blocks=[]
        while cursor<len(image):
            self.assertEqual(image[cursor],16)
            length=int.from_bytes(image[cursor+3:cursor+5],'little')
            cursor+=5
            blocks.append(image[cursor:cursor+length])
            cursor+=length
        self.assertEqual(len(blocks),2)
        raw=blocks[1][1:-1]
        cursor=0
        listing=[]
        while cursor<len(raw):
            number=int.from_bytes(raw[cursor:cursor+2],'big')
            size=int.from_bytes(raw[cursor+2:cursor+4],'little')
            cursor+=4
            listing.append((number,raw[cursor:cursor+size]))
            cursor+=size
        transformed,proof=specialize_glyph_data(listing,Kw(),None,Source(),Tap())
        self.assertEqual(len(proof),1)
        self.assertEqual(proof[0]['entries'],160)
        self.assertEqual([n for n,_ in listing], [n for n,_ in transformed])
        self.assertEqual(len([n for n,b in listing if dict(transformed)[n] != b]),5)
        self.assertNotEqual(dict(transformed)[9010],dict(listing)[9010])

    def test_wrong_count(self):
        rows,p=probe(GOOD[:-1]);self.assertFalse(p)
    def test_other_restore(self):
        rows,p=probe(GOOD+[(800,'RESTORE 9020')]);self.assertFalse(p)
    def test_jump_into_data(self):
        rows,p=probe(GOOD+[(800,'GO TO 9010')]);self.assertFalse(p)
    def test_computed_restore(self):
        rows,p=probe(GOOD+[(800,'RESTORE a')]);self.assertFalse(p)
    def test_unknown_data_variable(self):
        g=list(GOOD);g[2]=(9010,'DATA z,2,g,4,f,6,7,8');self.assertFalse(probe(g)[1])
    def test_outside_glyph_bounds(self):
        g=list(GOOD);g[1]=(9000,g[1][1].replace('"b"','"z"'));self.assertFalse(probe(g)[1])
    def test_unbounded_loop(self):
        g=list(GOOD);g[1]=(9000,g[1][1].replace('+7','+8'));self.assertFalse(probe(g)[1])

if __name__ == '__main__':unittest.main()