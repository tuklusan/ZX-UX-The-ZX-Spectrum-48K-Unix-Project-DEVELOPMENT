#!/usr/bin/env python3
"""Run SDK-compiled C48 programs on ZX-UX itself, loaded from cassette.

  python3 tests/ssxrun.py [--only a,b] [--png DIR] [--frames N] [-v]

For each program in sdk/tests/runs.json, use the source if it is available.
Otherwise, load the checked image from build/c48. Then make cassette
records, boot ZX-UX from the snapshot of the ROM
tape load (build/test.z80), log in, type /dev/cassette/NAME ARGS, play the
records on the emulated tape, type the scripted keys and check that the
program ran: its first screen appears (the shell's prompt is gone), it
reaches the expected text, and it hands the screen back when it exits.
A PNG of the screen is saved per program.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'sdk'))
import zxrun                       # noqa: E402
import rtap                        # noqa: E402
from rcc import driver             # noqa: E402
import rvm                         # noqa: E402
import suite                       # noqa: E402

RUNS = json.load(open(os.path.join(ROOT, 'sdk', 'tests', 'runs.json')))
SDK = os.environ.get('C48SDK') or os.path.normpath(os.path.join(ROOT, '..', 'tuklusan', 'zx-ux-c48-sdk'))
OUT = os.path.join(ROOT, 'build', 'ssx')
SCROWN = 0x5B63                    # kvars.inc: scrown = KV+99


def compile_prog(name, run):
    src = os.path.join(SDK, 'usr', 'src', run['dir'], run.get('src', name.split(':')[0]) + '.c')
    out = os.path.join(OUT, run.get('src', name.split(':')[0]) + '.ssx')
    if not os.path.isfile(src):
        ready = os.path.join(ROOT, 'build', 'c48', run.get('src', name.split(':')[0]) + '.ssx')
        if not os.path.isfile(ready):
            raise FileNotFoundError('C48 program source and built image are both missing')
        return open(ready, 'rb').read()
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        os.makedirs(OUT, exist_ok=True)
        if driver.main([src, '-o', out]):
            return None
    return open(out, 'rb').read()


def run_one(snap, name, run, pngdir, frames, verbose):
    ssx = compile_prog(name, run)
    if ssx is None:
        return False, 'compile failed'
    tname = run.get('src', name.split(':')[0])[:10]
    blocks = rtap.records(ssx, tname)
    s = suite.Session(snap)
    s.login()
    cmd = ' '.join(['/dev/cassette/' + tname] + run.get('args', []))
    s.zx.type(cmd + '\n')
    s.zx.tr.edges = zxrun.tape_pulses(blocks, s.zx.sim.registers[25] + 350000)
    # loading: pilots, pauses and about 2600 T-states a bit
    load_frames = (len(ssx) * 20600 + 32000000) // zxrun.FRAME + 400
    st = {'seen': False, 'last': None, 'gone': False, 'text': ''}
    mem = s.zx.mem

    def watch(n):
        for _ in range(n):
            if mem[SCROWN]:
                st['seen'] = True
                st['last'] = (bytes(mem[0x4000:0x5B00]), s.zx.tr.border)
            elif st['seen']:
                st['gone'] = True
                st['text'] = s.screen()
                return
            s.zx.run(1)
    watch(load_frames)
    if not st['seen']:
        scr = s.screen()
        last = [l for l in scr.splitlines()[:23] if l.strip()]
        return False, 'did not start: ' + (last[-1] if last else '?')
    keys = run.get('keys', '').encode().decode('unicode_escape')
    for ch in keys:
        watch(run.get('keygap', 100))
        if st['gone']:
            break
        s.zx.type(ch)
    if not st['gone']:
        watch(run.get('zxux_frames', max(frames, int(run.get('frames', 6000) * 1.5))))
    if not st['gone']:
        st['text'] = s.screen()
    scr, border = st['last']
    if pngdir:
        os.makedirs(pngdir, exist_ok=True)
        rvm.write_png(scr, os.path.join(pngdir, name.replace(':', '_') + '.ZX-UX.png'), border)
    ok = True
    why = []
    want = run.get('zxux_text', run.get('expect_text'))
    if want and want not in st['text']:
        ok = False
        why.append('no %r' % want)
    if verbose:
        print(st['text'])
    return ok, '; '.join(why) or ('exited' if st['gone'] else 'running')


def main(argv):
    only = None
    pngdir = os.path.join(ROOT, 'build', 'shots')
    frames = 1500
    verbose = False
    i = 0
    while i < len(argv):
        if argv[i] == '--only':
            only = set(argv[i + 1].split(','))
            i += 2
        elif argv[i] == '--png':
            pngdir = argv[i + 1]
            i += 2
        elif argv[i] == '--frames':
            frames = int(argv[i + 1])
            i += 2
        elif argv[i] == '-v':
            verbose = True
            i += 1
        else:
            i += 1
    snap = os.path.join(ROOT, 'build', 'test.z80')
    ok = total = 0
    for name, run in RUNS.items():
        if only and name not in only and name.split(':')[0] not in only:
            continue
        if run.get('ZX-UX') == 'skip':
            continue
        t = time.time()
        good, why = run_one(snap, name, run, pngdir, frames, verbose)
        total += 1
        ok += good
        print('%-14s %s %s (%.0fs)' % (name, 'PASS' if good else 'FAIL', why, time.time() - t))
    print('%d/%d ran on ZX-UX' % (ok, total))
    return 0 if ok == total else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
