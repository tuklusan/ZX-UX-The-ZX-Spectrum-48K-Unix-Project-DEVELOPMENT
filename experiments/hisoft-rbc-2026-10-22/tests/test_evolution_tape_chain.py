"""Audit the preserved Evolution stage transitions and native exec emission."""
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from evolution_tape_chain import stage_shape, allow_native_evolution_load, install

ROOT = Path(__file__).resolve().parents[3] / 'src/bonus/60-programs'
ARCHIVES = {
    '44-evolution-1': '8e72b017a3cd647829f84fbecdb4b8e26a3bc08b20da66ffb8ebaecd91ed14fb',
    '45-evolution-2': '623bc16f3749769f045e82f9f8f4369eaf18afacbeebd9f1fabad87a04409bf1',
}


def tape_lines(name):
    raw=(ROOT/name/'BASIC'/(name+'.tzx')).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==ARCHIVES[name]
    assert raw[:8]==b'ZXTape!\x1a'
    pos=10;blocks=[]
    while pos<len(raw):
        assert raw[pos]==0x10
        length=int.from_bytes(raw[pos+3:pos+5],'little')
        blocks.append(raw[pos+5:pos+5+length]);pos+=5+length
    assert len(blocks)==2
    data=blocks[1][1:-1]
    rows=[];pos=0
    while pos<len(data):
        number=int.from_bytes(data[pos:pos+2],'big')
        size=int.from_bytes(data[pos+2:pos+4],'little')
        rows.append((number,data[pos+4:pos+4+size]))
        pos+=4+size
    assert pos==len(data)
    return rows

class Finding:
    def __init__(self,line,operation='LOAD',severity='block',classification='tape_or_external_io'):
        self.line=line;self.operation=operation;self.severity=severity;self.classification=classification

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=tape_lines('44-evolution-1')
        cls.b=tape_lines('45-evolution-2')

    def test_original_sources_identified(self):
        self.assertEqual(stage_shape(self.a)['cassette_path'],'/dev/cassette/45-evoluti')
        self.assertEqual(stage_shape(self.b)['cassette_path'],'/dev/cassette/46-evoluti')
        self.assertEqual(stage_shape(self.a)['line'],8060)
        self.assertEqual(stage_shape(self.b)['line'],1860)

    def test_other_programs_not_exempted(self):
        self.assertIsNone(stage_shape([(10,b'\xef""\r')]))
        self.assertIsNone(stage_shape([(10,b'\xf5"HELLO"\r')]))

    def test_other_load_rejected(self):
        self.assertIsNone(stage_shape(self.a+[(9990,b'\xef""\r')]))
        self.assertIsNone(stage_shape(self.b+[(1990,b'\xef"GAME"\r')]))

    def test_wrong_input_or_menu_rejected(self):
        x=[(n,b.replace(b'="4"',b'="3"') if n==8060 else b) for n,b in self.a]
        self.assertIsNone(stage_shape(x))
        x=[(n,b.replace(b'4....Load stages 4&5.',b'4....Exit to shell.') if n==8010 else b) for n,b in self.a]
        self.assertIsNone(stage_shape(x))
        x=[(n,b.replace(b'="3"',b'="2"') if n==1860 else b) for n,b in self.b]
        self.assertIsNone(stage_shape(x))

    def test_quoted_load_not_an_additional_statement(self):
        x=self.a+[(8100,b'\xf5"LOAD is written in this prompt"\r')]
        self.assertEqual(stage_shape(x)['line'],8060)

    def test_single_memory_finding_only(self):
        q=[Finding(8060)]
        self.assertEqual(allow_native_evolution_load(self.a,q),1)
        self.assertEqual(q[0].classification,'native_next_cassette_exec')
        self.assertEqual(q[0].severity,'info')
        p=[Finding(1860)]
        self.assertEqual(allow_native_evolution_load(self.b,p),1)
        self.assertEqual(p[0].severity,'info')
        extras=[Finding(8060),Finding(77)]
        self.assertEqual(allow_native_evolution_load(self.a,extras),0)
        self.assertTrue(all(k.severity=='block' for k in extras))

    def test_unrecognized_syntax_not_downgraded(self):
        arr=[Finding(8060)]
        modified=[(n,b.replace(b'\xef""',b'\xef"file"') if n==8060 else b) for n,b in self.a]
        self.assertEqual(allow_native_evolution_load(modified,arr),0)
        self.assertEqual(arr[0].severity,'block')

    def test_native_exec_code_generation_and_private_bss(self):
        class Fake:
            @property
            def dispatch(self):return {}
            def reset(self,program):self.lines=program
            def layout_vars(self):self.pc=5000
            def __init__(self):
                self.emitted=[];self.line_no=8060
            def get_char(self):return self.characters[self.index]
            def next_char(self):
                self.index+=1
                return self.get_char()
            def at_end(self):return self.get_char()==13
            def ld_hl(self,n):self.emitted.append(('ld_hl',n))
            def emit(self,s,*a):self.emitted.append(('emit',s,a))
            def st_stop(self):self.emitted.append(('stop',))
            def not_supported(self,msg):raise ValueError(msg)
        class Module: Compiler=Fake
        install(Module)
        for name,rows in [('44-evolution-1',self.a),('45-evolution-2',self.b)]:
            c=Module.Compiler()
            c.reset(rows)
            c.layout_vars()
            shape=stage_shape(rows)
            self.assertEqual(c.pc-5000,len(shape['cassette_path'])+1)
            c.line_no=shape['line'];c.characters=b'""\r';c.index=0
            c.dispatch[0xef]()
            self.assertEqual(c.emitted[-1],('stop',))
            self.assertEqual(sum(x[1].count('call $6003') for x in c.emitted if x[0]=='emit'),3)
            # The native EXEC is syscall 11 with a NULL argv pointer.
            self.assertIn(('emit','ld de,0; ld a,11; call $6003',()),c.emitted)
            self.assertEqual(c.emitted.count(('ld_hl',5000)),2)
            # Check that the embedded path is all bytes, including terminal zero.
            literals=[x[2][0] for x in c.emitted if x[0]=='emit' and x[1]=='ld (hl),{}; inc hl']
            self.assertEqual(bytes(literals),shape['cassette_path'].encode()+b'\0')
            self.assertEqual(c.emitted[-1][0],'stop')

    def test_load_expression_rejected_in_emitter(self):
        class Fake:
            @property
            def dispatch(self):return {}
            def reset(self,program):self.lines=program
            def layout_vars(self):self.pc=10
            def get_char(self):return self.characters[self.i]
            def next_char(self):self.i+=1;return self.get_char()
            def at_end(self):return self.get_char()==13
            def not_supported(self,msg):raise ValueError(msg)
        class Module: Compiler=Fake
        install(Module)
        c=Fake();c.reset(self.a);c.layout_vars();c.line_no=8060
        for string in (b'"NEXT"\r',b'"" CODE\r',b'X$\r'):
            c.characters=string;c.i=0
            with self.assertRaises(ValueError):c.st_load()

if __name__=='__main__':unittest.main()