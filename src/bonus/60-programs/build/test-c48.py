#!/usr/bin/env python3
"""Small independent source and real-ZX-UX smoke checks for the two C48 pilots.

python build/test-c48.py --system /path/to/ZX-UX.tzx [--sdk /path/to/sdk]
The system image must have its matching kernel.json beside it.  This script
only writes throwaway emulator cache under the ignored build/tmp directory.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / 'build' / 'tmp'


def glyphs(path: Path):
    return {int(n): tuple(int(x) for x in v.split(','))
            for v, n in re.findall(r'\bdb ([0-9,]+)\s*; (\d+)', path.read_text())}


def check_sources():
    """Independent source/BASIC-data review (no reuse of game code)."""
    for number, stem, first, last in ((25, 'galaxian', 9010, 9300),
                                       (58, 'invaders', 1030, 1090)):
        directory = next(ROOT.glob(f'{number:02d}-*'))
        bas = (directory / 'BASIC' / (directory.name + '.bas')).read_text()
        data = []
        for line in bas.splitlines():
            m = re.match(r'^(\d+) DATA (.*)$', line)
            if not m or not first <= int(m[1]) <= last:
                continue
            values = re.split(r',\s*', m[2])
            for item in values:
                item = item.strip()
                data.append(int(item[4:], 2) if item.startswith('BIN ') else int(item))
        table = glyphs(directory / 'C48' / (stem + '-glyphs.asm'))
        if number == 25:
            original = [b for n in sorted(table) for b in table[n]]
            assert data == original, f'{directory.name}: BASIC DATA sprites differ'
        else:
            # BASIC READ assigns consecutive DATA bytes to several glyphs
            # interleaved by scanline; the port stores each glyph contiguously.
            layout = ((1030, (128, 129)), (1040, (130, 131)),
                      (1050, (132, 136)), (1060, (133, 135)),
                      (1070, (134,)), (1080, (137, 138, 139)),
                      (1090, (140,)))
            lines = {int(m.group(1)): [int(z) for z in m.group(2).split(',')]
                     for m in re.finditer(r'^(\d+) DATA ([\d,]+)$', bas, re.M)}
            for line_no, codes in layout:
                chunk = lines[line_no]
                assert len(chunk) == 8 * len(codes)
                for k, code in enumerate(codes):
                    actual = tuple(chunk[row * len(codes) + k] for row in range(8))
                    assert table[code] == actual, f'{directory.name}: sprite {code} differs from BASIC DATA {line_no}'
        source = (directory / 'C48' / (stem + '.c')).read_text()
        assert not re.search(r'getchar\s*\(\s*\)\s*;', source), f'{stem}: buffered terminal input on a game prompt'
        assert 'fresh_key();' in source, f'{stem}: missing fresh-key gate'
    gal = (ROOT / '25-galaxians' / 'C48' / 'galaxian.c').read_text()
    player_laser = gal.split('static void fire_laser(void)', 1)[1].split('static void game_over_msg(void)', 1)[0]
    enemy_laser = gal.split('static void enemy_fire(void)', 1)[1].split('static void round_init(void)', 1)[0]
    assert 'plot(sx,8)' not in player_laser, 'Galaxians duplicates DRAW start pixel with PLOT'
    assert 'plot(col*8,y0)' not in enemy_laser, 'Galaxians duplicates enemy DRAW start pixel'
    assert 'draw(sx,8,sx,138)' in player_laser and 'draw(col*8,y0,col*8,9)' in enemy_laser

    inv = (ROOT / '58-invaders' / 'C48' / 'invaders.c').read_text()
    assert 'ch(19,shotcol,97)' not in inv, 'ASCII a used in place of a rocket'
    assert 'ship_active' in inv and 'code>=132 && code<=136' in inv
    assert 141 in glyphs(ROOT / '58-invaders' / 'C48' / 'invaders-glyphs.asm')
    print('PASS: two BASIC sprite tables; fresh-key gates; rocket and ship source audit')


def cell(scr, row, col):
    return tuple(scr[((row & 24) << 8) + (scan << 8) + ((row & 7) << 5) + col]
                 for scan in range(8))


def test_kernel(system: Path, sdk: Path, captures=False):
    sys.dont_write_bytecode = True
    os.environ['ZXUX_RVM_CACHE'] = str(TMP / 'test-c48-cache')
    sys.path.insert(0, str(sdk))
    import rvm
    from zxux import char_keys
    font = glyphs(ROOT / 'c48lib' / 'c48lib-font.asm')
    decode = {v: chr(k) for k, v in font.items()}

    def text(scr, row):
        return ''.join(decode.get(cell(scr, row, c), '?') for c in range(32))

    def launch(program, stem):
        opt = rvm.Options()
        opt.prog = str(ROOT / program / 'C48' / (stem + '.ssx'))
        opt.system = str(system)
        opt.headless, opt.mute = True, True
        runner = rvm.Runner(opt)
        runner.start()
        for _ in range(3000):
            runner.frame()
            if runner.fg.started is not None:
                break
        else:
            raise AssertionError(f'{stem}: program did not start through ZX-UX')
        return runner

    def step_to(runner, elapsed):
        while runner.session.m.frame - runner.fg.started < elapsed:
            runner.frame()
        return runner.picture()[0]

    space = ('SPACE',)
    gal = launch('25-galaxians', 'galaxian')
    intro = step_to(gal, 135)
    assert 'Fleet after fleet' in text(intro, 2), 'Galaxians intro missing'
    gal.session.kb.add([('press', space, 20)])
    started = step_to(gal, 220)
    assert 'SCORE:' in text(started, 0), 'Galaxians did not leave intro'
    go = step_to(gal, 960)
    assert 'PRESS ANY KEY TO PLAY AGAIN' in text(go, 18), 'Galaxians game-over prompt missing'
    hold = step_to(gal, 1080)
    assert 'PRESS ANY KEY TO PLAY AGAIN' in text(hold, 18), 'Galaxians auto-restarted without a new press'
    if captures:
        rvm.write_png(hold, str(ROOT / '25-galaxians' / 'C48' / 'SCREENSHOTS'
                                / '04-C48-GAME-OVER-WAIT.png'), gal.picture()[1])
    gal.session.kb.add([('press', space, 20)])
    restarted = step_to(gal, 1170)
    assert 'PRESS ANY KEY TO PLAY AGAIN' not in text(restarted, 18), 'Galaxians failed a fresh restart'
    print('PASS: Galaxians ZX-UX intro, fresh start, stable game-over, fresh restart')
    # Regress the missile endpoint on actual ZX-UX screen RAM. The frozen
    # console may reserve row 22, so source inspection above is also required.
    shot = launch('25-galaxians', 'galaxian')
    step_to(shot, 135)
    shot.session.kb.add([('press', space, 20)])
    baseline = step_to(shot, 220)
    assert cell(baseline, 22, 17)[7] & 1 == 0, 'dirty laser start pixel before firing'
    shot.session.kb.add([('press', char_keys('m'), 20)])
    after_shot = step_to(shot, 295)
    assert cell(after_shot, 22, 17)[7] & 1 == 0, 'laser left a bottom-row pixel'
    print('PASS: Galaxians pixel endpoint after firing; redundant PLOT source guard')


    inv = launch('58-invaders', 'invaders')
    intro = step_to(inv, 135)
    assert 'I N V A D E R S' in text(intro, 0), 'Invaders intro missing'
    inv.session.kb.add([('press', space, 15)])
    step_to(inv, 200)
    sprites = glyphs(ROOT / '58-invaders' / 'C48' / 'invaders-glyphs.asm')
    missile = sprites[141]
    alien = sprites[130]
    fired = False
    movement = 0
    flight = False
    trace = []
    for _ in range(700):
        scr = inv.picture()[0]
        elapsed = inv.session.m.frame - inv.fg.started
        col = next((c for c in range(32) if cell(scr, 20, c) == alien), None)
        position = None if col is None else col - 1
        if position is not None and (not trace or trace[-1][1] != position):
            trace.append((elapsed, position))
        if not fired and not inv.session.kb.busy() and elapsed > 205:
            if position is not None and position < 2:
                inv.session.kb.add([('press', char_keys('8'), 9), ('wait', 20)])
                movement += 1
            elif position > 2:
                inv.session.kb.add([('press', char_keys('5'), 4), ('wait', 22)])
                movement += 1
            elif position == 2:
                inv.session.kb.add([('press', char_keys('7'), 22), ('wait', 30)])
                fired = True
        if fired and not flight and any(cell(scr, row, c) == missile
                                        for row in range(19) for c in range(32)):
            flight = True
            if captures:
                rvm.write_png(scr, str(ROOT / '58-invaders' / 'C48' / 'SCREENSHOTS'
                                        / '04-C48-ROCKET-FLIGHT.png'), inv.picture()[1])
        inv.frame()
        if fired and not inv.session.kb.busy() and elapsed > 340:
            break
    hud = text(inv.picture()[0], 21)
    assert movement >= 2 and fired, f'Invaders movement/fire not reached: {movement}/{fired}, positions {trace}'
    assert flight, 'Invaders rocket did not visibly climb the screen'
    assert 'ROCKET RESERVE:59' in hud, f'Invaders fire did not consume one rocket: {hud!r}'
    assert 'SCORE:20' in hud, f'Invaders hit did not score 20: {hud!r}'
    assert hud[10:15] == '     ', f'Invaders HUD has ghost text: {hud!r}'
    if captures:
        rvm.write_png(inv.picture()[0], str(ROOT / '58-invaders' / 'C48'
                                              / 'SCREENSHOTS' / '05-C48-SCORED-HIT.png'), inv.picture()[1])
    # Aim at the empty column between formation pairs.  The shot must miss,
    # cost 10 points and one rocket, and leave no transient MISS! HUD text.
    inv.session.kb.add([('press', char_keys('8'), 8), ('wait', 25)])
    step_to(inv, inv.session.m.frame - inv.fg.started + 45)
    miss_col = next((c for c in range(32) if cell(inv.picture()[0], 20, c) == alien), None)
    assert miss_col == 4, f'Invaders could not align miss shot: {miss_col!r}'
    inv.session.kb.add([('press', char_keys('7'), 20), ('wait', 35)])
    step_to(inv, inv.session.m.frame - inv.fg.started + 130)
    miss_hud = text(inv.picture()[0], 21)
    assert 'SCORE:10' in miss_hud and 'ROCKET RESERVE:58' in miss_hud, (
        f'Invaders miss did not cost 10 points and a rocket: {miss_hud!r}')
    assert miss_hud[10:15] == '     ', f'Invaders miss left HUD garbage: {miss_hud!r}'
    before = next((c for c in range(32) if cell(inv.picture()[0], 20, c) == alien), None)
    inv.session.kb.add([('press', ('CS', '8'), 20), ('wait', 35)])
    step_to(inv, inv.session.m.frame - inv.fg.started + 80)
    after = next((c for c in range(32) if cell(inv.picture()[0], 20, c) == alien), None)
    assert before is not None and after is not None and after >= before + 5, (
        f'Invaders CAPS SHIFT+8 fast movement failed: {before!r} to {after!r}')
    print('PASS: Invaders ZX-UX movement, rocket, hit, miss, clean HUD, shifted move')


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--sdk', type=Path, default=ROOT.parent.parent / 'zx-ux-sdk')
    arg.add_argument('--system', type=Path, help='actual ZX-UX.tzx with matching kernel.json')
    arg.add_argument('--captures', action='store_true', help='record three actual frames inside C48/SCREENSHOTS')
    a = arg.parse_args()
    check_sources()
    if a.system:
        test_kernel(a.system.resolve(), a.sdk.resolve(), a.captures)
    else:
        print('NOTE: emulator tests skipped (supply --system for mandatory runtime gate)')


if __name__ == '__main__':
    main()
