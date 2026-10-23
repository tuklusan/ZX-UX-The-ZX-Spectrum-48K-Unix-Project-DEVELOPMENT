"""Preserved Picture Pairs input, literal attribute bounds and rejection cases."""
from __future__ import annotations
import hashlib
from pathlib import Path
import sys
import unittest
from dataclasses import dataclass
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from picture_attrs import adapt_picture_attrs, allow_bounded_picture_attributes

TOKEN={0xe9:'DIM',0xf1:'LET',0xee:'INPUT',0xeb:'FOR',0xcc:'TO',
       0xf3:'NEXT',0xe3:'READ',0xe4:'DATA',0xed:'GO SUB',0xec:'GO TO',
       0xf4:'POKE',0xfa:'IF',0xcb:'THEN',0xc5:'OR',0xb1:'LEN',0xc0:'USR',
       0xc2:'CHR$',0xa5:'RND',0xba:'INT',0xaf:'CODE',0xfe:'RETURN',
       0xe2:'STOP',0xf5:'PRINT',0xc6:'AND',0xb0:'VAL',0xdd:'INVERSE'}
class Kw:
    TOKEN=TOKEN
    CODE_FOR={v:k for k,v in TOKEN.items()}
class Source:
    @staticmethod
    def hide_numbers(b,fp):
        n=int(b)
        return b+b'\x0e\x00\x00'+n.to_bytes(2,'little')+b'\x00'
class Tap:
    @staticmethod
    def split_lines(program):
        if isinstance(program,list):return list(program)
        rows=[];i=0
        while i<len(program):
            n=int.from_bytes(program[i:i+2],'big')
            length=int.from_bytes(program[i+2:i+4],'little')
            rows.append((n,program[i+4:i+4+length]));i+=4+length
        assert i==len(program)
        return rows
    @staticmethod
    def join_lines(rows):return list(rows)
@dataclass
class Finding:
    line:int
    expression:str
    severity:str='block'
    classification:str='unbounded_memory_write'
    operation:str='POKE'
ROOT=Path(__file__).resolve().parents[3]/'src/bonus/60-programs/27-picture-pairs/BASIC/27-picture-pairs.tzx'

def original_rows():
    source=ROOT.read_bytes()
    assert hashlib.sha256(source).hexdigest()=='0b20705fc318840e29056eb63df95a03a2b1ebc9b26f434398c3d2208f2ae494'
    assert source.startswith(b'ZXTape!\x1a')
    pos=10;blocks=[]
    while pos<len(source):
        assert source[pos]==16
        n=int.from_bytes(source[pos+3:pos+5],'little')
        blocks.append(source[pos+5:pos+5+n]);pos+=5+n
    assert len(blocks)==2
    return Tap.split_lines(blocks[1][1:-1])

def findings():
    return [Finding(n,s) for n,s in (
        (210,'Z+T(Y)+U(X),W'),(260,'Z+T(X)+U(Y),W'),
        (307,'Z+T(P)+U(X),40'),(335,'Z+T(P)+U(X),40'),
        (520,'Z+T(Q)+U(X),V'),(520,'Z+T(P)+U(X),V'),
        (530,'Z+T(P)+U(X),57'))]
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=original_rows()
    def adapt(self,rows=None):
        return adapt_picture_attrs(self.rows if rows is None else rows,Kw(),None,Source(),Tap())
    def test_source_unchanged_and_guard_only_line_330(self):
        new,proof=self.adapt()
        self.assertEqual([p['attribute_write_count'] for p in proof],[7])
        self.assertEqual([(p['address_min'],p['address_max']) for p in proof],[(22595,23161)])
        original=dict(self.rows); changed=dict(new)
        self.assertEqual([n for n,b in self.rows if b!=changed[n]],[330])
        self.assertTrue(changed[330].startswith(original[330][:-1]))
        self.assertIn(bytes((Kw.CODE_FOR['STOP'],)),changed[330])
        self.assertEqual(original[210],changed[210]);self.assertEqual(original[520],changed[520])
    def test_seven_bound_display_writes_only(self):
        new,proof=self.adapt();self.assertTrue(proof)
        fs=findings()
        self.assertEqual(allow_bounded_picture_attributes(new,TOKEN,fs),7)
        self.assertTrue(all(f.severity=='info' and
                            f.classification=='bounded_screen_attribute_write' for f in fs))
    def test_no_guard_means_no_memory_exemption(self):
        fs=findings()
        self.assertEqual(allow_bounded_picture_attributes(self.rows,TOKEN,fs),0)
        self.assertTrue(all(f.severity=='block' for f in fs))
    def test_altered_attribute_offset_fails(self):
        rows=[(n,b.replace(b'66\x0e',b'99\x0e') if n==2050 else b)
              for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
    def test_altered_screen_pointer_fails(self):
        rows=[(n,b.replace(b'22595\x0e',b'30000\x0e') if n==200 else b)
              for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
    def test_extra_array_writer_fails(self):
        self.assertFalse(self.adapt(self.rows+[(209,b'\xf1T(1)=999\r')])[1])
    def test_extra_poke_fails(self):
        self.assertFalse(self.adapt(self.rows+[(209,b'\xf4Z+1,255\r')])[1])
    def test_missing_index_validation_fails(self):
        rows=[(n,b'\xed540\x0e\x00\x00\x1c\x02\x00\r' if n==330 else b)
              for n,b in self.rows]
        self.assertFalse(self.adapt(rows)[1])
    def test_incomplete_findings_remain_blocked(self):
        new,_=self.adapt();fs=findings()[:-1]
        self.assertEqual(allow_bounded_picture_attributes(new,TOKEN,fs),0)
        self.assertTrue(all(f.severity=='block' for f in fs))
    def test_changed_finding_remains_blocked(self):
        new,_=self.adapt();fs=findings();fs[0].expression='Z+T(Y)+U(X)+500,W'
        self.assertEqual(allow_bounded_picture_attributes(new,TOKEN,fs),0)
        self.assertTrue(all(f.severity=='block' for f in fs))
if __name__=='__main__':unittest.main()