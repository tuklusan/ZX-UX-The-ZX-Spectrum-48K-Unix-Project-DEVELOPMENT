#!/usr/bin/env python3
"""ZX-UX beta-0.1.0 cassette and new-game checks on the real Z80 kernel.

Run after building: python3 -B tests/test_beta010_release.py
Only the replay setup adjusts test RAM; it never changes a screenshot or binary.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'release/dist/sdk/bin/py'),
                str(ROOT / 'release/src/zx-ux-sdk'), str(ROOT / 'tests')]
import zxux
import rvm
import cassette_beta7
import ras
import rtap
import rld
from rcc import driver

GAME = ROOT / 'release/dist/assets/c48-bin/ssx/invaders.ssx'
CFILE = ROOT / 'release/dist/assets/c48-src/games/invaders.c'
ASM = ROOT / 'release/dist/assets/c48-src/games/invaders.asm'
LIB = ROOT / 'release/build/sdk/lib/libc48.ssa'
GLYPHS = bytes((0, 31, 63, 63, 123, 113, 225, 225,
                0, 248, 252, 252, 222, 142, 135, 135))


def shell_check():
    s = zxux.Session()
    s.boot()
    reads = s.m.tape_requests
    s.kb.type('/dev/cassette/\n')
    s.run_until(lambda: 'missing cassette program name' in s.text(),
                450, 'empty cassette-name error')
    assert s.m.tape_requests == reads, 'Empty name read the tape'
    s.wait_prompt()
    tape = cassette_beta7.member(125, version=5, name='demo')
    s.m.cassette.extend(tape)
    s.kb.type('tar xf /dev/cassette/archive\n')
    s.wait_prompt(1600)
    assert 'Extracting: /tmp/x' in s.text(), 'Archive filename was not printed'
    s.m.cassette.extend(tape)
    s.kb.type('tar tf /dev/cassette/archive\n')
    s.wait_prompt(1600)
    listing = s.text().split('# tar tf /dev/cassette/archive')[-1].split('#')[0]
    assert listing.count('/tmp/x') == 1 and 'Extracting:' not in listing, 'Listing changed'
    print('PASS cassette: bare name, extract display, unchanged listing', flush=True)


def ball_check():
    o = rvm.Options()
    o.prog = str(ROOT / 'release/dist/assets/c48-bin/ssx/ball.ssx')
    o.headless = True
    r = rvm.Runner(o)
    r.start()

    def area(scr, col1, col2):
        result = bytearray()
        for y in range(32, 160):
            pos = ((y & 0xc0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
            result += scr[pos + col1:pos + col2]
        return bytes(result)

    prior = left = None
    for _ in range(1600):
        r.frame()
        if r.fg.started is None:
            continue
        elapsed = r.session.m.frame - r.fg.started
        if elapsed >= 150 and prior is None:
            pixels = r.session.m.screen()
            prior, left = area(pixels, 16, 32), area(pixels, 0, 16)
        if prior is not None and elapsed >= 370:
            pixels = r.session.m.screen()
            assert sum(x != y for x, y in zip(prior, area(pixels, 16, 32))) > 20, \
                'BALL did not animate'
            assert left == area(pixels, 0, 16), 'BALL changed the shell panel'
            print('PASS BALL: animation on the right, left panel intact', flush=True)
            return
    raise AssertionError('BALL never reached animation samples')


def wildcard_check():
    s = zxux.Session()
    s.boot()
    program = (ROOT / 'release/dist/assets/c48-bin/ssx/ball.ssx').read_bytes()
    assert s.m.mem[0x5890] != 56, 'BALL panel already present'
    s.m.cassette.extend(rtap.records(program, 'ball'))
    s.kb.type('/dev/cassette/*\n')
    s.run_until(lambda: s.m.mem[0x5890] == 56, 600,
                'first eligible executable from explicit wildcard')
    print('PASS cassette: explicit * loads BALL from tape', flush=True)


def symbol_map():
    asm, _, _ = driver.compile_to_asm(str(CFILE), {'udgs': 32})
    cobj = rld.Obj(ras.assemble_text(asm, 'invaders-c.s'), 'c')
    zobj = rld.Obj(ras.assemble_text(ASM.read_text(), 'invaders-asm.s'), 'asm')
    library = rld.read_archive(LIB.read_bytes(), str(LIB))
    image, _, _, symbols, _ = rld.link([cobj, zobj], [library], 'start', 800, 0)
    assert image == GAME.read_bytes(), 'Native link does not match released game'
    return symbols


def new_runner():
    o = rvm.Options()
    o.prog = str(GAME)
    o.keys = 'm'
    o.keygap = 160
    o.headless = True
    r = rvm.Runner(o)
    r.start()
    for _ in range(1000):
        r.frame()
        if r.fg.started is not None and not r.session.kb.busy() \
                and occupied_cols(r.session.m.screen()):
            return r
    raise AssertionError('Game never reached active play')


def occupied_cols(scr):
    return [x for x in range(32)
            if sum(bool(scr[((y & 0xc0) << 5) | ((y & 7) << 8) |
                            ((y & 0x38) << 2) | x]) for y in range(168, 176)) >= 3]


def advance(r, count):
    for _ in range(count):
        r.frame()


def offset_mem(r, symbols, name):
    mem = r.session.m.mem
    position = mem.find(GLYPHS, 0x6000)
    assert position >= 0x6000, 'Native glyph block missing from RAM'
    base = position - symbols['_shapes'][0]
    return base + symbols[name][0]


def game_check(symbols):
    r = new_runner()
    first = occupied_cols(r.session.m.screen())
    r.session.kb.add([('press', ('c',), 20)])
    advance(r, 55)
    right = occupied_cols(r.session.m.screen())
    r.session.kb.add([('press', ('z',), 18)])
    advance(r, 55)
    left = occupied_cols(r.session.m.screen())
    assert first and right and left
    assert min(right) > min(first), 'C did not move right'
    assert min(left) < min(right), 'Z did not move left'

    bullet = offset_mem(r, symbols, '_bullet_row')
    mem = r.session.m.mem
    before = int.from_bytes(mem[bullet:bullet + 2], 'little', signed=True)
    r.session.kb.add([('press', ('m',), 30)])
    fired = False
    for _ in range(75):
        r.frame()
        value = int.from_bytes(mem[bullet:bullet + 2], 'little', signed=True)
        if 10 <= value <= 20 and value > before:
            fired = True
            break
    assert fired, 'M did not start a missile'
    print('PASS Invaders: M start, C right, Z left, M fire', flush=True)


def replay_check(symbols):
    for key in ('n', 'y'):
        r = new_runner()
        s = r.session
        mem = s.m.mem
        life = offset_mem(r, symbols, '_lives')
        mem[life:life + 2] = bytes((0, 0))  # enter real replay path quickly
        s.run_until(lambda: 'PLAY AGAIN? (Y/N)' in s.text(),
                    800, 'real game-over replay prompt')
        s.kb.add([('press', (key,), 30)])
        if key == 'n':
            for _ in range(500):
                r.frame()
                if r.fg.ended is not None:
                    break
            assert r.fg.ended is not None and r.fg.status == 0, 'N did not exit'
        else:
            s.run_until(lambda: 'SCORE' in s.text() and
                        'PLAY AGAIN' not in s.text(), 500, 'Y replay restart')
            assert r.fg.ended is None, 'Y did not restart the game'
    print('PASS Invaders: Y restart, N exit through native keyboard', flush=True)


def main():
    shell_check()
    wildcard_check()
    ball_check()
    symbols = symbol_map()
    game_check(symbols)
    replay_check(symbols)
    print('PASS beta-0.1.0 game and cassette regression checks', flush=True)


if __name__ == '__main__':
    main()
