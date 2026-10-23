"""Prove nine literal UDG shapes and reject unsafe memory inputs."""
import sys,unittest
from pathlib import Path
from dataclasses import dataclass
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from test_stellar_charset import original_rows, KW, Tape
from stellar_charset import adapt_stellar_charset,_TOKEN_NAMES
from udg_data_literals import allow_literal_data_udgs

TOKEN=dict(_TOKEN_NAMES);TOKEN.update({0xeb:'FOR',0xcc:'TO',0xe3:'READ',0xf3:'NEXT',0xe4:'DATA',0xc0:'USR'})
@dataclass
class Finding:
    line:int
    operation:str
    expression:str
    classification:str
    severity:str='block'

def pair():
    return [Finding(8100,'POKE','USR A$+B,C','unbounded_memory_write'),
            Finding(8100,'USR','A$+B,C','raw_machine_code_address')]

def effective_rows(source_rows=None):
    rows=original_rows() if source_rows is None else source_rows
    rows,_=adapt_stellar_charset(rows,KW(),None,None,Tape())
    return [(n,bytes((0xea,))+b'\r' if n==1010 else b) for n,b in rows]

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=effective_rows()
    def proof(self,rows=None,findings=None):
        return allow_literal_data_udgs(self.rows if rows is None else rows,
                                       TOKEN,pair() if findings is None else findings)
    def test_literal_data_glyphs(self):
        f=pair();self.assertEqual(self.proof(findings=f),2)
        self.assertEqual([x.severity for x in f],['info','info'])
        self.assertEqual([x.classification for x in f],
                         ['bounded_data_udg_write','process_udg_pointer'])
    def test_unadapted_global_pointer_fails(self):
        self.assertEqual(self.proof(original_rows()),0)
    def test_changed_data_byte_fails(self):
        rows=[(n,b.replace(b'255\x0e',b'300\x0e') if n==8020 else b)
              for n,b in self.rows]
        self.assertEqual(self.proof(rows),0)
    def test_duplicate_data_source_fails(self):
        self.assertEqual(self.proof(self.rows+[(8005,b'\xe4"a",0\r')]),0)
    def test_altered_user_glyph_expression_fails(self):
        rows=[(n,b.replace(b'\xc0a$+b,c',b'\xc0a$+b+128,c') if n==8100 else b)
              for n,b in self.rows]
        self.assertEqual(self.proof(rows),0)
    def test_second_raw_pointer_fails(self):
        f=pair()+[Finding(8100,'USR','B$+Z','raw_machine_code_address')]
        self.assertEqual(self.proof(findings=f),0)
        self.assertTrue(all(x.severity=='block' for x in f))
    def test_no_pair_no_approval(self):
        f=pair()[:-1]
        self.assertEqual(self.proof(findings=f),0)
        self.assertEqual(f[0].severity,'block')
    def test_changed_init_loop_fails(self):
        rows=[(n,b.replace(b'\xc0a$+b,c',b'\xc0a$+b+1,c') if n==8100 else b)
              for n,b in self.rows]
        self.assertEqual(self.proof(rows),0)
if __name__=='__main__':unittest.main()