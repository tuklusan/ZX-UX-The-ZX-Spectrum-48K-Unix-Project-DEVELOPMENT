#!/usr/bin/env python3
"""Per-program checks for experimental Minelay C48 translation.

Run with: python test-minelay.py --system /path/to/ZX-UX.tzx --sdk /path/to/sdk/bin/py
The SDK must contain the frozen rvm.py and a matching ZX-UX system description.
"""
import argparse
import os
from pathlib import Path
import re
import sys

THIS = Path(__file__).resolve().parent
ROOT = THIS.parent.parent

def check_glyphs():
    data = []
    source = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    for row in source.splitlines():
        found = re.match(r'^(9010|9020|9030|9040) DATA (.*)$', row)
        if found:
            data.extend(int(v.strip()) for v in found[2].split(','))
    local = []
    for row in (THIS / 'minelay-glyphs.asm').read_text().splitlines():
        found = re.search(r'\bdb ([0-9,]+)', row)
        if found:
            local.extend(int(v) for v in found[1].split(','))
    assert len(data) == 56 and data == local, 'Original BASIC sprite bitmap mismatch'
    print('PASS: 7 original BASIC glyphs independently match all 56 bytes')

def check_screen(system, sdk):
    sys.dont_write_bytecode = True
    os.environ['ZXUX_RVM_CACHE'] = str(ROOT / 'build' / 'tmp' / 'minelay-rvm-cache')
    sys.path.insert(0, str(sdk))
    import rvm
    from zxux import char_keys
    opt = rvm.Options()
    opt.prog = str(THIS / 'minelay.ssx')
    opt.system = str(system)
    opt.headless = True
    opt.mute = True
    runner = rvm.Runner(opt)
    runner.start()
    for _ in range(4000):
        runner.frame()
        if runner.fg.started is not None:
            break
    else:
        raise AssertionError('Minelay did not start under ZX-UX kernel')
    def step(frames):
        for _ in range(frames):
            runner.frame()
        return runner.picture()[0]
    intro = step(135)
    idle = step(40)
    assert intro == idle, 'Minelay intro advanced without user input'
    runner.session.kb.add([('press', ('SPACE',), 20)])
    menu = step(95)
    assert menu != idle, 'Minelay did not reach difficulty selection'
    runner.session.kb.add([('press', char_keys('2'), 20)])
    gameplay = step(115)
    assert gameplay != menu, 'Minelay did not draw active maze after choice 2'
    runner.session.kb.add([('press', char_keys('p'), 20)])
    after_input = step(55)
    assert after_input != gameplay, 'Minelay did not respond to P movement'
    print('PASS: real ZX-UX Minelay intro/idle, menu, maze, movement')

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--system',type=Path)
    cli.add_argument('--sdk',type=Path)
    a = cli.parse_args()
    check_glyphs()
    if a.system and a.sdk:
        check_screen(a.system.resolve(), a.sdk.resolve())
    else:
        print('NOT RUN: real-kernel test needs --system and --sdk')
if __name__ == '__main__':
    main()
