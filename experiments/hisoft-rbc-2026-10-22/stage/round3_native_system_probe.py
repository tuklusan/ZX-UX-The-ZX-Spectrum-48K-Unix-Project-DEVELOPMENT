"""Real ZX-UX Phase B native RUN and shell font-restore probes.

Compile from untracked numbered Sinclair BASIC fixtures; require actual SSX1
linking and kernel startup.  Never modify the published game corpus.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT/'build/tmp/rbc-round3'
sys.path.insert(0,str(ROOT/'src/zx-ux-sdk'))
import rvm
import rld


def compile_one(name: str, listing: str):
    src=WORK/(name+'.bas')
    dest=WORK/(name+'.ssx')
    src.write_text(listing, encoding='ascii')
    args=[sys.executable,str(WORK/'current/rbc/rbc.py'),str(src),
          '--frontend',str(WORK/'upstream'),'--sdk','src/zx-ux-sdk',
          '--rom','src/zx-ux-sdk/rom/48.rom',
          '--tape',str(WORK/'hisoft48.tap'),'-o',str(dest)]
    result=subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if result.returncode!=0:
        raise RuntimeError(f'{name} native compilation failed: {result.stderr[-700:]}')
    d=dest.read_bytes()
    rld.parse_ssx(d)
    print(name, 'linked',len(d),'sha256',hashlib.sha256(d).hexdigest(),flush=True)
    return dest


def execute(ssx: Path):
    result=rvm.run_kernel(ssx,frames=850,
                          system=ROOT/'build/out/ZX-UX.tzx',cache=True)
    if result.why!='exit':
        print(ssx.stem,'unexpected runtime state:',result.why,
              'PC',hex(result.session.m.cpu.pc),'SP',hex(result.session.m.cpu.sp),
              'program',result.fg.describe(),
              'syscalls',result.session.syscalls,flush=True)
    low=result.session.m.mem[0x5c36]
    high=result.session.m.mem[0x5c37]
    picture,_=result.picture()
    from zxscreen import screen_text
    screen=screen_text(picture)
    print(ssx.stem,'kernel exit',result.fg.status,'CHARS',hex(low+(high<<8)),
          'screen',repr(screen[-250:]),flush=True)
    return low+(high<<8),screen,result


def main():
    basic=compile_one('rbc-r3-control', '10 PRINT "CONTROL"\n20 STOP\n')
    run=compile_one('rbc-r3-run',
        '10 LET A=7\n'
        '20 POKE 23692,42\n'
        '30 RUN 100\n'
        '40 PRINT "BAD0"\n'
        '50 STOP\n'
        '100 IF A<>0 THEN GO TO 400\n'
        '110 IF PEEK 23692<>42 THEN GO TO 400\n'
        '120 PRINT "RUN OK"\n'
        '130 STOP\n'
        '400 GO TO 400\n')
    font=compile_one('rbc-r3-font',
        '10 POKE 23606,0: POKE 23607,128\n'
        '20 PRINT "FONT"\n'
        '30 STOP\n')
    control_ptr,_,control_result=execute(basic)
    run_ptr,run_screen,run_result=execute(run)
    font_ptr,_,font_result=execute(font)
    if any(res.why!='exit' for res in (control_result,run_result,font_result)):
        raise RuntimeError('at least one real ZX-UX STOP did not exit')
    if len({control_ptr,run_ptr,font_ptr})!=1:
        raise RuntimeError('process CHARS state contaminated subsequent shell')
    print('Native RUN and font return-to-shell checks PASS',flush=True)


if __name__=='__main__':
    main()