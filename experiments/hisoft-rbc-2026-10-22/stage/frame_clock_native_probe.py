#!/usr/bin/env python3
"""Observe real ZX-UX syscall-38 use in preserved game executables.

This is a diagnostic, not a gameplay pass. Only real CPU syscall hooks and
frames from the frozen emulator are recorded. A missing call is not promoted
into a successful timer test.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path


def probe(root: Path, binary: Path, control: str, budget: int=4800):
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
    import rvm
    import zxux
    opt = rvm.Options()
    opt.prog = str(binary)
    opt.system = str(root / 'dist/zx-ux/tzx/ZX-UX.tzx')
    opt.cache = True
    opt.headless = True
    opt.mute = True
    runner = rvm.Runner(opt)
    state = {'program': binary.stem, 'executable_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
             'emulator':'frozen ZX-UX', 'syscall_number':38, 'tick_calls':[],
             'frames_executed':0, 'foreground_started':False, 'screen_changed':False,
             'validation':'not-yet-proven'}
    try:
        runner.start()
        sysaddr=runner.session.system.syscall
        original=runner.session.m.hooks[sysaddr]
        def inspect_call(machine):
            if machine.cpu.a == 38:
                state['tick_calls'].append({'frame':machine.frame,
                                             'after_start':runner.fg.started is not None})
            return original(machine)
        runner.session.m.hooks[sysaddr]=inspect_call
        initial=None
        samples=set()
        sent=0
        first_start=None
        for i in range(budget):
            runner.frame()
            state['frames_executed']=i+1
            if runner.fg.started is not None and first_start is None:
                first_start=runner.session.m.frame
                initial=hashlib.sha256(runner.picture()[0]).hexdigest()
            if first_start is not None:
                elapsed=runner.session.m.frame-first_start
                if elapsed in (80,250,500,1000,2000,3000):
                    samples.add(hashlib.sha256(runner.picture()[0]).hexdigest())
                # Repeated original keys during the real intro avoids guessing
                # at which frame a BEEP/PRINT loop reaches its prompt.
                if elapsed in (180,520,860,1200,1540,1880,2220,2560,2900):
                    runner.session.kb.add([('press', zxux.char_keys(control), 20)])
                    sent+=1
                if runner.fg.ended is not None:
                    break
        state['foreground_started']=first_start is not None
        state['screen_changed']=bool(initial and any(s!=initial for s in samples))
        state['keypresses_sent']=sent
        state['foreground_ended']=runner.fg.ended
        state['foreground_status']=runner.fg.status
        state['tick_calls_after_start']=sum(x['after_start'] for x in state['tick_calls'])
        if state['tick_calls_after_start']:
            state['validation']='native-kernel-tick-syscall-observed'
    except Exception as exc:
        state['error']=type(exc).__name__+': '+str(exc)
    return state


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--trial',type=Path,required=True)
    parser.add_argument('--shard',type=int,required=True)
    args=parser.parse_args()
    targets=((0,'06-motocross-tape.ssx','1'),(2,'32-buzzy-bee-tape.ssx',' '))
    results=[]
    for shard,name,control in targets:
        if shard!=args.shard:
            continue
        binary=args.trial/name
        if not binary.exists():
            results.append({'program':name,'validation':'not-run','reason':'compiler output missing'})
            continue
        results.append(probe(args.root,binary,control))
    path=args.trial/f'frame-clock-native-shard-{args.shard}.json'
    path.write_text(json.dumps(results,indent=2)+'\n')
    for item in results:
        print('CLOCK_NATIVE',json.dumps(item),flush=True)
    # Diagnostics do not claim a pass without seeing genuine syscall events;
    # scorekeeping remains the strict compiler/native-start checks.

if __name__=='__main__':
    main()
