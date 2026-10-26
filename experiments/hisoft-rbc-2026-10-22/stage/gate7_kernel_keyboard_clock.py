"""Native Z80 keyboard matrix and frame-tick probes on the real ZX-UX kernel.

This tests hardware/kernel behavior, not BASIC compiler input handling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import ras
import rld
import rvm
import zxux

CLOCK = '''    section text
    global start
start:
    ld a,38
    call 0x6003
    push hl
    ei
    halt
    halt
    ld a,38
    call 0x6003
    pop de
    or a
    sbc hl,de
    jr z,failed
    ld hl,0
    jr exit
failed:
    ld hl,11
exit:
    ld a,1
    call 0x6003
    ret
'''
KEYBOARD = '''    section text
    global start
start:
    ld a,38
    call 0x6003
    ld (first_tick),hl
poll:
    ld a,0xfe
    in a,(0xfe)
    and 2
    jr z,pressed
    ld a,38
    call 0x6003
    ld de,(first_tick)
    or a
    sbc hl,de
    ld a,h
    or a
    jr nz,timeout
    ld a,l
    cp 80
    jr c,poll
timeout:
    ld hl,11
    jr exit
pressed:
    ld hl,0
exit:
    ld a,1
    call 0x6003
    ret
    section bss
first_tick: ds 2
'''


def link(work: Path):
    files, stats = {}, {}
    for name, listing in (('clock', CLOCK), ('keyboard', KEYBOARD)):
        obj = rld.Obj(ras.assemble_text(listing), name+'.sso')
        data, _, _, _, _ = rld.link([obj], [], stack=384)
        result = rld.parse_ssx(data)
        total = len(result['image']) + result['bss'] + result['stack']
        if max(len(data), total) > 12000:
            raise RuntimeError(name + ': exceeds default memory limit')
        target = work / (name + '.ssx')
        target.write_bytes(data)
        files[name] = target
        stats[name] = {'file':len(data), 'image':len(result['image']),
                       'bss':result['bss'], 'stack':result['stack'], 'total':total,
                       'sha256':hashlib.sha256(data).hexdigest()}
    return files, stats


def run(system: Path, work: Path):
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('missing native kernel metadata')
    if system.read_bytes() != (ROOT/'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('kernel differs from frozen release')
    work.mkdir(parents=True,exist_ok=True)
    files, stats = link(work)
    opt = rvm.Options()
    opt.prog = str(files['clock'])
    opt.system = str(system)
    opt.cache = True
    runner = rvm.Runner(opt)
    runner.start()
    s = runner.session
    baseline = (s.word(0x5c36),s.word(0x5c7b))
    records=[]
    scenarios = [('clock',0,False), ('keyboard',11,False),
                 ('keyboard',0,True), ('keyboard',11,False)]
    for index,(name, expected, press) in enumerate(scenarios):
        path=files[name]
        job=runner.fg if index == 0 else s.launch(path.read_bytes(),zxux.program_name(str(path)))
        fired=False
        for _ in range(4200):
            runner.frame()
            if press and job.started is not None and job.ended is None and not fired:
                if s.m.frame-job.started >= 8:
                    s.kb.add([('press',zxux.char_keys('z'),24)])
                    fired=True
            if job.ended is not None:
                break
        if not (job.started is not None and job.ended is not None and
                job.status==expected and not s.owns_screen(job.pid)):
            raise RuntimeError('native '+name+' exit mismatch: '+str({
                'expected':expected,'actual':job.status,'started':job.started,
                'ended':job.ended,'pressed':fired}))
        if (s.word(0x5c36),s.word(0x5c7b)) != baseline:
            raise RuntimeError('shell graphics leaked after '+name)
        records.append({'program':name,'expected':expected,'status':job.status,
                        'pressed':fired,'frames':job.ended-job.started,
                        'screen_released':True})
        # Consume any held key before running the no-key case.
        if press:
            for _ in range(32):
                runner.frame()
            if s.kb.state != 'idle':
                raise RuntimeError('physical key did not release')
    return {'linked':stats,'runs':records,'shell_chars':baseline[0],
            'shell_udg':baseline[1]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--system',type=Path,default=ROOT/'build/out/ZX-UX.tzx')
    parser.add_argument('--work',type=Path,default=ROOT/'build/tmp/rbc-gate7-keyboard')
    args=parser.parse_args()
    print('GATE7_KERNEL_KEYBOARD_CLOCK',json.dumps(run(args.system,args.work),sort_keys=True))

if __name__=='__main__':
    main()
