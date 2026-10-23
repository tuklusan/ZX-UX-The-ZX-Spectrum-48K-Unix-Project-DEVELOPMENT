"""Real tape and mock code-generation checks for Stellar Run's CHARS view."""
from pathlib import Path
import hashlib
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage'))
from stellar_charset import adapt_stellar_charset, install, _shape, _TOKEN_NAMES

class KW:
    TOKEN=_TOKEN_NAMES
    CODE_FOR={v:k for k,v in TOKEN.items()}
class Tape:
    @staticmethod
    def split_lines(b):
        if isinstance(b,list):return list(b)
        p=0;rows=[]
        while p<len(b):
            n=int.from_bytes(b[p:p+2],'big')
            l=int.from_bytes(b[p+2:p+4],'little')
            rows.append((n,b[p+4:p+4+l]));p+=4+l
        assert p==len(b)
        return rows
    @staticmethod
    def join_lines(rows):return list(rows)
ROOT=Path(__file__).resolve().parents[3]/'src/bonus/60-programs/52-stellar-run/BASIC/52-stellar-run.tzx'
def original_rows():
    src=ROOT.read_bytes()
    assert hashlib.sha256(src).hexdigest()=='765ae45397f894327e7fbb543ae2cdfd3d13946510076534cc4fc209a88610f2'
    assert src.startswith(b'ZXTape!\x1a')
    p=10;blocks=[]
    while p<len(src):
        assert src[p]==16
        size=int.from_bytes(src[p+3:p+5],'little')
        blocks.append(src[p+5:p+5+size]);p+=5+size
    assert len(blocks)==2
    return Tape.split_lines(blocks[1][1:-1])
class TestStellarCharset(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rows=original_rows()
    def convert(self,rows=None):
        return adapt_stellar_charset(self.rows if rows is None else rows,KW(),None,None,Tape())
    def test_exact_tape_and_two_inert_line_changes(self):
        new,proof=self.convert()
        self.assertEqual(len(proof),1)
        self.assertTrue(proof[0]['restore_before_return'])
        self.assertEqual([n for n,b in self.rows if b!=dict(new)[n]],[120,140])
        self.assertEqual(dict(new)[120],bytes((0xea,))+b'\r')
        self.assertEqual(dict(new)[140],bytes((0xea,))+b'\r')
        self.assertTrue(_shape(new,_TOKEN_NAMES,True))
        self.assertEqual(dict(new)[130],dict(self.rows)[130])
    def test_changed_first_pointer_rejected(self):
        rows=[(n,b.replace(b'23675\x0e',b'23575\x0e') if n==120 else b)
              for n,b in self.rows]
        self.assertFalse(self.convert(rows)[1])
    def test_changed_second_pointer_rejected(self):
        rows=[(n,b.replace(b'60\x0e',b'61\x0e') if n==140 else b)
              for n,b in self.rows]
        self.assertFalse(self.convert(rows)[1])
    def test_extra_global_write_rejected(self):
        rows=self.rows+[(190,b'\xf423606,0\r')]
        self.assertFalse(self.convert(rows)[1])
    def test_extra_screen_probe_rejected(self):
        rows=[(n,b.replace(b'+112\x0e',b'+113\x0e') if n==130 else b)
              for n,b in self.rows]
        self.assertFalse(self.convert(rows)[1])
    def test_bypass_charset_line_rejected(self):
        rows=self.rows+[(189,b'\xec130\r')]
        self.assertFalse(self.convert(rows)[1])
    def test_other_program_unmodified(self):
        rows=[(10,b'\xf5"HELLO"\r')]
        self.assertEqual(self.convert(rows),(rows,[]))
    def test_generated_rom_call_balanced_and_scoped(self):
        class Fake:
            def __init__(self):self.events=[];self.line_no=130
            def reset(self,program):self.lines=program
            def emit(self,code):self.events.append(('emit',code))
            def fn_screen(self):self.events.append(('original',))
            def next_char(self):self.events.append(('next',))
            def two_ints_bc(self):self.events.append(('coords',))
            def _string_result(self,target):self.events.append(('screen',target))
        class Mod:
            Compiler=Fake
            ROM={'SCREEN':0x2888}
        install(Mod)
        p=Mod.Compiler(); rows,pr=self.convert();self.assertTrue(pr)
        p.reset(rows);self.assertTrue(p._zxux_stellar_screen)
        p.fn_screen()
        self.assertEqual(p.events[0:3],[('next',),('coords',),('next',)])
        self.assertEqual(p.events[4],('screen',0x2888))
        pre=p.events[3][1];post=p.events[5][1]
        self.assertIn('di;',pre);self.assertIn('ld hl,($5C7B)',pre)
        self.assertIn('push hl',pre);self.assertIn('ld ($5C36),hl',pre)
        self.assertIn('pop hl',post);self.assertIn('ei',post)
        p.events=[];p.line_no=110;p.fn_screen()
        self.assertEqual(p.events,[('original',)])
if __name__=='__main__':unittest.main()