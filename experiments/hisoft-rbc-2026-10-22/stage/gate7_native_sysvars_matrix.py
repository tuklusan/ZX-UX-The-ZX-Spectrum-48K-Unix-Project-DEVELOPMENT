"""Native Gate 7 Z80 virtual system-variable checks in the real ZX-UX kernel."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
STAGE=ROOT/'experiments/hisoft-rbc-2026-10-22/stage'
sys.path[:0]=[str(STAGE),str(ROOT/'src/zx-ux-sdk')]
from native_sysvars_rt import _native_peek,_native_poke,BSS_BYTES
import functools, subprocess, tempfile

def assembler(tool, temporary):
    @functools.lru_cache(maxsize=400)
    def assemble(source):
        lines=source.replace(';','\n').splitlines()
        with tempfile.TemporaryDirectory(dir=temporary) as tmp:
            asm=Path(tmp)/'code.asm'; binary=Path(tmp)/'code.bin'
            asm.write_text('    org 0\n'+''.join('    '+line.strip()+'\n' for line in lines if line.strip()))
            completed=subprocess.run([str(tool),'--nologo','--raw='+str(binary),str(asm)],text=True,capture_output=True,timeout=30)
            if completed.returncode or not binary.is_file():
                raise RuntimeError('Z80 assembler failed: '+completed.stdout+completed.stderr)
            return binary.read_bytes()
    return assemble
import rld,rvm

BASES=(0x5000,0x6000,0x7000)

class Emitter:
    def __init__(self): self.code=bytearray();self.patch=[];self.labels={}
    def op(self,*data):self.code.extend(data)
    def label(self,name):self.labels[name]=len(self.code)
    def word(self,value):self.code.extend((value&255,(value>>8)&255))
    def ldhl(self,addr):self.op(0x21);self.word(addr)
    def poke(self,address,value):
        self.ldhl(address);self.op(0x1e,value,0xcd);self.patch.append((len(self.code),'poke'));self.word(0)
    def peek_eq(self,address,value):
        self.ldhl(address);self.op(0xcd);self.patch.append((len(self.code),'peek'));self.word(0)
        self.op(0x7d,0xfe,value,0xc2);self.patch.append((len(self.code),'failure'));self.word(0)
    def peek_ne(self,address,value):
        self.ldhl(address);self.op(0xcd);self.patch.append((len(self.code),'peek'));self.word(0)
        self.op(0x7d,0xfe,value,0xca);self.patch.append((len(self.code),'failure'));self.word(0)
    def construct(self,base,asm):
        self.label('done');self.op(0xc9)
        self.label('failure');from native_error_exit import error_exit_bytes
        self.code.extend(error_exit_bytes(11))
        lead_size=len(self.code)
        p0=_native_poke(asm,0,base,0,entry=lead_size)
        k0=_native_peek(asm,0,base,0,entry=lead_size+len(p0))
        bss=lead_size+len(p0)+len(k0)
        poke=_native_poke(asm,bss,base,bss+BSS_BYTES,entry=lead_size)
        peek=_native_peek(asm,bss,base,bss+BSS_BYTES,entry=lead_size+len(poke))
        if len(poke)!=len(p0) or len(peek)!=len(k0):raise RuntimeError('emitter changed length')
        self.labels['poke']=lead_size;self.labels['peek']=lead_size+len(poke)
        for offset,label in self.patch:self.code[offset:offset+2]=(base+self.labels[label]).to_bytes(2,'little')
        return bytes(self.code)+poke+peek,bss

def program(base,asm):
    e=Emitter()
    for addr,value in ((0x5c6a,0x55),(0x5c39,0x23),(0x5c8c,0x5a)):
        e.poke(addr,value)
    for addr,value in ((0x5c6a,0x55),(0x5c39,0x23),(0x5c8c,0x5a)):
        e.peek_eq(addr,value)
    # Set the virtual 24-bit counter to 0xFFFFFF and exercise rollover.
    for addr in (0x5c78,0x5c79,0x5c7a):e.poke(addr,255)
    e.op(0xfb,0x76,0x76,0x76) # EI + 3 real interrupt intervals
    for addr in (0x5c79,0x5c7a):e.peek_eq(addr,0)
    e.peek_ne(0x5c78,255)
    code,bss=e.construct(base,asm)
    return code,bss

def run(compiler,tool,system,work):
    if not (compiler/'rbc.py').is_file():raise RuntimeError('missing reconstructed RBC')
    if not tool.is_file():raise RuntimeError('missing Z80 assembler')
    if system.read_bytes() != (ROOT/'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():raise RuntimeError('wrong native kernel')
    if not system.with_name('kernel.json').is_file():raise RuntimeError('missing kernel metadata')
    sys.path.insert(0,str(compiler));import rbc
    work.mkdir(parents=True,exist_ok=True)
    asm=assembler(tool,work)
    builds=[]
    for base in BASES:
        code,bss=program(base,asm)
        builds.append(rbc.HiSoftBuild(code,base,base,BSS_BYTES))
    output,meta=rbc.build_ssx(builds,bytes(768),rld,384,use_rom_font=True)
    parsed=rld.parse_ssx(output)
    sizes={'file':len(output),'image':len(parsed['image']),'bss':parsed['bss'],'stack':parsed['stack'], 'total':len(parsed['image'])+parsed['bss']+parsed['stack'], 'sha256':hashlib.sha256(output).hexdigest()}
    if max(sizes['file'],sizes['total'])>12000:raise RuntimeError('memory limit exceeded')
    path=work/'virtual-sysvars.ssx';path.write_bytes(output)
    opts=rvm.Options();opts.prog=str(path);opts.system=str(system);opts.cache=True
    runner=rvm.Runner(opts);runner.start();session=runner.session
    initial=(session.word(0x5c36),session.word(0x5c7b))
    original={a:session.m.mem[a] for a in [0x5c6a,0x5c39,0x5c8c,0x5c78,0x5c79,0x5c7a]}
    rows=[]
    for i in range(3):
        job=runner.fg if i==0 else session.launch(output,rvm.zxux.program_name(str(path)))
        for _ in range(4200):
            runner.frame()
            if job.ended is not None:break
        row={'started':job.started,'ended':job.ended,'status':job.status,'screen_released':not session.owns_screen(job.pid)}
        if job.started is None or job.ended is None or job.status!=0 or not row['screen_released']:
            raise RuntimeError('native process failed '+str(row))
        if (session.word(0x5c36),session.word(0x5c7b)) != initial:raise RuntimeError('shell pointers leaked')
        if {a:session.m.mem[a] for a in original} != original:raise RuntimeError('protected native system vars changed')
        rows.append(row)
    return {'dimensions':sizes,'runs':rows,'virtual_variables':['FLAGS2','PIP','SCR_CT','FRAMES rollover'],'protected_unchanged':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path,default=ROOT/'build/tmp/rbc-checkpoint-recovered/rbc');p.add_argument('--assembler',type=Path,required=True);p.add_argument('--system',type=Path,default=ROOT/'build/out/ZX-UX.tzx');p.add_argument('--work',type=Path,default=ROOT/'build/tmp/rbc-gate7-sysvars-matrix');x=p.parse_args();print('GATE7_NATIVE_SYSVARS',json.dumps(run(x.compiler.resolve(),x.assembler.resolve(),x.system.resolve(),x.work.resolve()),sort_keys=True))
