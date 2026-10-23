"""Real original frame-counter uses and isolated-process compiler redirect."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'stage'))
from process_frame_clock import timer_shape,allow_virtual_frame_clock,install

ROOT=Path(__file__).resolve().parents[3]
DIGEST={
    '06-motocross':'119f29f00c0caee152254f0578dabaa04511d12dffffe4f354d4431643d7f7ad',
    '32-buzzy-bee':'ca11a8363bcf6373ed1dcd0fcfd83bde3fd753a4f50e666e3d568c1a8a6704ed',
}


def read_tape(name):
    path=ROOT/'src/bonus/60-programs'/name/'BASIC'/(name+'.tzx')
    blob=path.read_bytes()
    assert hashlib.sha256(blob).hexdigest()==DIGEST[name]
    assert blob.startswith(b'ZXTape!\x1a')
    blocks=[];pos=10
    while pos<len(blob):
        assert blob[pos]==16
        size=int.from_bytes(blob[pos+3:pos+5],'little')
        blocks.append(blob[pos+5:pos+5+size]);pos+=5+size
    prog=blocks[1][1:-1];rows=[];pos=0
    while pos<len(prog):
        number=int.from_bytes(prog[pos:pos+2],'big')
        length=int.from_bytes(prog[pos+2:pos+4],'little')
        rows.append((number,prog[pos+4:pos+4+length]));pos+=4+length
    assert pos==len(prog)
    return rows


@dataclass
class Finding:
    line:int
    operation:str
    severity:str
    classification:str
    expression:str


def findings(lines):
    setup,read=timer_shape(lines)
    results=[]
    for addr in (23674,23673,23672):
        results.append(Finding(setup,'POKE','block','global_memory_write',f'{addr},255'))
        results.append(Finding(read,'PEEK','block','global_memory_read',str(addr)))
    return results

class TimerTests(unittest.TestCase):
    def test_real_tapes_are_independently_verified(self):
        for name,expected in (('06-motocross',(25,2000)),('32-buzzy-bee',(50,1503))):
            with self.subTest(name=name):
                lines=read_tape(name)
                self.assertEqual(timer_shape(lines),expected)
                checks=findings(lines)
                self.assertEqual(allow_virtual_frame_clock(lines,checks),6)
                self.assertTrue(all(x.classification=='process_frame_clock' for x in checks))

    def test_modified_address_and_extra_access_are_not_accepted(self):
        lines=read_tape('06-motocross')
        invalid=lines+[(9001,b'\xf423672,255\r')]
        self.assertIsNone(timer_shape(invalid))
        checks=findings(lines)
        checks.pop()
        self.assertEqual(allow_virtual_frame_clock(lines,checks),0)
        self.assertTrue(all(x.severity=='block' for x in checks))

    def test_elapsed_ticks_are_modular_and_reset_independent(self):
        mod=1<<24
        for start,now,want in ((100,100,mod-1),(100,149,48),
                               (mod-2,2,3),(12345,12345+49,48)):
            self.assertEqual((now-start-1)%mod,want)


class StubCompiler:
    def __init__(self):
        self.lines=[]
        self._zxux_frame_shape=(25,2000)
        self._zxux_frame_base=1000
        self.line_no=25
        self.buf=bytearray(b'23672\x0e\x00\x00\x78\x5c\x00,255\x0e\x00\x00\xff\x00\x00\r')
        self.ch=0
        self.ops=[]
        self.pc=100
        self.t=None
    def reset(self,prog): self.lines=prog
    def layout_vars(self): self.pc=100
    def st_poke(self): raise AssertionError('raw shared-memory write')
    def fn_peek(self): raise AssertionError('raw shared-memory read')
    def number_to_hl(self):
        import re
        m=re.match(rb'(\d+)\x0e.{5}', self.buf[self.ch:])
        assert m is not None, (self.ch,self.buf)
        self.ch+=m.end()
        return int(m[1])
    def next_char(self):
        self.ch+=1
        return self.buf[self.ch]
    def emit(self,*args): self.ops.append(('emit',)+args)
    def emit_op_reloc(self,*args): self.ops.append(('reloc',)+args)

class StubModule:
    Compiler=StubCompiler
    POSINT=2

class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):install(StubModule)

    def test_relocatable_timer_snapshot_only(self):
        c=StubModule.Compiler()
        c.st_poke()
        self.assertEqual(c.ch, len(c.buf)-1)
        self.assertEqual(c.ops, [
            ('emit','ld hl,($5C78)'),('reloc','ld (nn),hl',1000),
            ('emit','ld a,($5C7A)'),('reloc','ld (nn),a',1002)])

    def test_timing_byte_reads_use_process_offset(self):
        for address in (23672,23673,23674):
            c=StubModule.Compiler()
            c.line_no=2000
            c.buf=bytearray(str(address).encode()+b'\x0e\0\0\0\0\0\r')
            c.fn_peek()
            self.assertEqual(c.t,StubModule.POSINT)
            self.assertEqual(c.ops[1],('reloc','ld de,(nn)',1000))
            self.assertEqual(c.ops[3],('reloc','ld a,(nn)',1002))
            self.assertTrue(any('sbc hl,de' in x[1] for x in c.ops if x[0]=='emit'))
            self.assertFalse(any('ld ($5C7' in str(x) for x in c.ops))

    def test_nonmatching_address_not_virtualized(self):
        c=StubModule.Compiler()
        c.buf=bytearray(b'23675,255\r')
        with self.assertRaisesRegex(AssertionError,'raw shared-memory write'):
            c.st_poke()

if __name__=='__main__':unittest.main()
