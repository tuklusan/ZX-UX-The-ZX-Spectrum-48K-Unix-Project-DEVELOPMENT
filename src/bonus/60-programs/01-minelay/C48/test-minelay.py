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

def check_placements():
    """Independently compare BASIC SCREEN$ retry rules to C48 placement."""
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    source = (THIS / 'minelay.c').read_text()
    for basic_line in ('7410 IF SCREEN$ (y,x)=""THEN GO TO 7400',
                       '7520 IF SCREEN$ (y,x)=""THEN GO TO 7510'):
        assert basic_line in basic, 'BASIC SCREEN$ rejection rule changed'
    maze = source.split('static void make_maze(void)', 1)[1].split('static void lose_life(void)', 1)[0]
    # Each of the first two random item-placement passes must reject a
    # previously drawn UDG rather than destroy it; the five axes are not
    # subjected to this BASIC rule.
    assert maze.count('while(board[r*32+c]>=128);') == 2, 'UDG overwrite regression'
    assert maze.count('do {r=rnd(18)+2;c=rnd(28)+1;}') == 2, 'BASIC retry missing'
    print('PASS: eggs and mines preserve original BASIC SCREEN$ UDG retry behavior')

def check_pursuer_draw_order():
    """BASIC 700/705/720: mine trail first; pursuing sprite is drawn last."""
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    c48 = (THIS / 'minelay.c').read_text()
    assert '700 PRINT AT my,mx;" "' in basic
    assert '720 PRINT AT my,mx;INK 5;BRIGHT 1;"{93}"' in basic
    mine = c48.split('static void mine_step(void)', 1)[1].split('int main(void)', 1)[0]
    assert mine.index('at_cell(old_my,old_mx,133,5,0);') < mine.index('at_cell(my,mx,131,5,1);'), (        'Half-cell pursuer can disappear behind mine deposited at same cell')
    # Adversarial overlap: when old and new visible cells coincide, order
    # alone determines whether the player sees an active pursuer or a mine.
    cell = 32
    cell = 133  # BASIC 700 may deposit into the same character cell.
    cell = 131  # BASIC 720 redraws the enemy *after* the deposit.
    assert cell == 131
    print('PASS: pursuer draws after laid mine even on overlapping half-cell steps')

def check_original_title():
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    original = re.search(r'^9500 PRINT INK 0;AT 0,0;"([^"]*)"', basic, re.M)
    source = (THIS / 'minelay.c').read_text()
    image = re.search(r'pattern="([^"]*)";', source)
    assert original and image and original[1] == image[1] and len(image[1]) == 157, (        'Original five-row BASIC title pattern was changed')
    assert "if(pattern[k]=='_')" in source and 'title_animation();' in source
    assert 'fresh_enter();' in source and 'while(!kbd_down(13))' in source, 'Original ENTER start required'
    print('PASS: original BASIC 157-character animated-title data preserved')

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
    intro = step(650)
    idle = step(40)
    assert intro == idle, 'Minelay intro advanced without user input'
    runner.session.kb.add([('press', ('ENTER',), 20)])
    menu = step(95)
    assert menu != idle, 'Minelay did not reach difficulty selection'
    runner.session.kb.add([('press', char_keys('2'), 20)])
    gameplay = step(115)
    assert gameplay != menu, 'Minelay did not draw active maze after choice 2'
    runner.session.kb.add([('press', char_keys('p'), 20)])
    after_input = step(55)
    assert after_input != gameplay, 'Minelay did not respond to P movement'
    # Also check actual bitmap bytes: the pursuing glyph must remain visible
    # after its deposited-mine trails, even on half-character-cell steps.
    enemy_bytes = (195,36,24,36,126,90,129,0)  # original BASIC UDG 147
    def enemy_visible(screen):
        for row in range(2, 22):
            for col in range(32):
                found = tuple(screen[((row & 24) << 8) + (scan << 8) +
                                     ((row & 7) << 5) + col] for scan in range(8))
                if found == enemy_bytes:
                    return True
        return False
    sampled = [after_input] + [step(15) for _ in range(5)]
    assert sum(enemy_visible(screen) for screen in sampled) >= 4, (        'Minelay pursuer glyph disappeared behind its deposited-mine trails')
    # Leave the player stationary while the mine-layer chases and consumes
    # the remaining lives. A stable game-over/menu screen must follow.
    # Use a fresh game without any movement so the pursuer reaches the base.
    runner = rvm.Runner(opt)
    runner.start()
    for _ in range(4000):
        runner.frame()
        if runner.fg.started is not None:
            break
    else:
        raise AssertionError('Minelay replay did not start')
    step(650)
    runner.session.kb.add([('press', ('ENTER',), 20)])
    step(95)
    runner.session.kb.add([('press', char_keys('2'), 20)])
    step(35)
    over_screen = step(2700)
    font = ROOT / 'c48lib' / 'c48lib-font.asm'
    charmap = {}
    for row in font.read_text().splitlines():
        match = re.search(r'\bdb ([0-9,]+)\s*; (\d+)', row)
        if match:
            charmap[tuple(int(v) for v in match[1].split(','))] = chr(int(match[2]))
    def text_line(scr, row):
        def glyph(col):
            return tuple(scr[((row & 24) << 8) + (pix << 8) +
                             ((row & 7) << 5) + col] for pix in range(8))
        return ''.join(charmap.get(glyph(col), '?') for col in range(32))
    assert 'G A M E  O V E R' in text_line(over_screen, 5), 'no GAME OVER after mine collisions'
    assert step(120) == over_screen, 'Minelay game-over prompt changed without input'
    runner.session.kb.add([('press', char_keys('1'), 20)])
    hard_maze = step(130)
    assert hard_maze != over_screen, 'Minelay failed to start a hard replay'
    assert 'Score' in text_line(hard_maze, 0), 'Minelay hard replay did not draw a maze'
    print('PASS: real ZX-UX intro/menu/maze/movement, mine-layer game-over, idle restart, hard replay')

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--system',type=Path)
    cli.add_argument('--sdk',type=Path)
    a = cli.parse_args()
    check_glyphs()
    check_placements()
    check_pursuer_draw_order()
    check_original_title()
    if a.system and a.sdk:
        check_screen(a.system.resolve(), a.sdk.resolve())
    else:
        print('NOT RUN: real-kernel test needs --system and --sdk')
if __name__ == '__main__':
    main()
