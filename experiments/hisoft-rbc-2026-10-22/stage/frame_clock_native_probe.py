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
                tick_event={'frame':machine.frame,
                            'after_start':runner.fg.started is not None}
                state['tick_calls'].append(tick_event)
                sp=machine.cpu.sp
                return_address=machine.mem[sp] | (machine.mem[(sp+1)&65535]<<8)
                old_return_hook=machine.hooks.get(return_address)
                def measure_return(mm):
                    # Remove the hook on its first invocation. Otherwise
                    # a hot game loop would count thousands of false returns.
                    if old_return_hook is None:
                        mm.hooks.pop(return_address,None)
                    else:
                        mm.hooks[return_address]=old_return_hook
                    tick_event['ticks_returned']=(mm.cpu.h<<8)|mm.cpu.l
                    return old_return_hook(mm) if old_return_hook else False
                machine.hooks[return_address]=measure_return
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
        native_calls=[x for x in state['tick_calls'] if x['after_start']]
        ticks=[x['ticks_returned'] for x in native_calls if 'ticks_returned' in x]
        state['tick_calls_after_start']=len(native_calls)
        state['distinct_returned_ticks']=len(set(ticks))
        state['timer_measurement_passed']=(first_start is not None
            and state['screen_changed'] and len(native_calls)>=3
            and len(ticks)==len(native_calls) and len(set(ticks))>=2)
        if state['timer_measurement_passed']:
            state['validation']='native-tick-values-advance-with-gameplay'
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
    # Put native execution readings beside the corresponding per-input record.
    shard_records=args.trial/f'rbc-60-results-shard-{args.shard}.json'
    if shard_records.exists():
        rows=json.loads(shard_records.read_text())
        for item in results:
            for row in rows:
                if row['program']==item['program'].removesuffix('.ssx'):
                    row['frame_clock_native']=item
        shard_records.write_text(json.dumps(rows,indent=2)+'\n')
    failures=[item for item in results if item.get('validation')!='not-run'
              and not item.get('timer_measurement_passed')]
    if failures:
        raise RuntimeError('Native game frame clock did not advance: '+
                           ', '.join(x['program'] for x in failures))

if __name__=='__main__':
    main()
