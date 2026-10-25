"""Fail-closed symbolic emission and actual-size reduction fixtures."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'stage'))
from upeepz80_codegen import optimize_fragment

class Optimizer:
    def optimize(self, source):
        if source == '    ld a,0\n    or b\n':
            return '    xor a\n    or b\n'
        return source
def asm(src):
    table = {'ld a,0':b'\x3e\x00','xor a':b'\xaf','or b':b'\xb0',
             'jp 40000':b'\xc3\x40\x9c','jr +2':b'\x18\x02',
             'ld b,a':b'\x47','ld h,l':b'\x65'}
    return b''.join(table[ins.strip().lower()] for ins in src.split(';'))

class Tests(unittest.TestCase):
    def test_symbolic_before_encoding_reduces_size(self):
        self.assertEqual(optimize_fragment('ld a,0; or b',Optimizer(),asm),
                         ('xor a; or b',1))
    def test_jump_targets_are_never_rewritten(self):
        for frag in ('jp 40000; ld b,a','jr +2; ld h,l'):
            self.assertEqual(optimize_fragment(frag,Optimizer(),asm),(frag,0))
    def test_single_instruction_is_unchanged(self):
        self.assertEqual(optimize_fragment('ld a,0',Optimizer(),asm),('ld a,0',0))
    def test_no_optimization_leaves_bytes_intact(self):
        frag='ld b,a; ld h,l'
        self.assertEqual(optimize_fragment(frag,Optimizer(),asm),(frag,0))

if __name__ == '__main__': unittest.main()
