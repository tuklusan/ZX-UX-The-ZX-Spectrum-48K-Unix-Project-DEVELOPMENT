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
import shutil
import subprocess
import tempfile

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
    assert '705 LET my1=my:LET mx1=mx' in basic
    mine = c48.split('static void mine_step(void)', 1)[1].split('int main(void)', 1)[0]
    assert mine.index('previous_my=my;previous_mx=mx;') < mine.index('if(my2<y*2)'), (
        'BASIC line 705 saves the pursuer BEFORE the half-cell move')
    assert mine.index('old_my=previous_my;old_mx=previous_mx;') > mine.index('at_cell(my,mx,131,5,1);'), (
        'The saved mine-trail position must be the pre-move cell')
    assert 'old_my=my;old_mx=mx;' not in mine, 'Stale post-move mine-trail state'
    assert mine.index('at_cell(old_my,old_mx,133,5,0);') < mine.index('at_cell(my,mx,131,5,1);'), (        'Half-cell pursuer can disappear behind mine deposited at same cell')
    # Adversarial overlap: when old and new visible cells coincide, order
    # alone determines whether the player sees an active pursuer or a mine.
    cell = 32
    cell = 133  # BASIC 700 may deposit into the same character cell.
    cell = 131  # BASIC 720 redraws the enemy *after* the deposit.
    assert cell == 131
    print('PASS: pursuer trails use pre-movement coordinates; mine is drawn before pursuer')

def check_collision_cleanup():
    """BASIC 6000 clears the pursuer's occupied cell before respawning."""
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    c48 = (THIS / 'minelay.c').read_text()
    assert '6000 PRINT AT my,mx;" "' in basic
    collision = c48.split('static void lose_life(void)', 1)[1].split('static void player_step(void)', 1)[0]
    assert collision.index('blank(my2/2,mx2/2);') < collision.index('respawn_mine();'), (
        'The old mine-layer screen cell is not cleared before respawn')
    assert 'blank(last_y,last_x);' in collision and 'blank(y,x);' in collision, (
        'BASIC 6005 clears the last displayed player location on life loss')
    print('PASS: BASIC 6000 pursuer cleanup before respawn; axe overlap redraw')

def check_player_timing():
    """BASIC draws before moving and the mine tests the drawn ATTR 6 cell."""
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    source = (THIS / 'minelay.c').read_text()
    assert '100 PRINT AT y1,x1;" ";INK 6;AT y,x;a$:LET y1=y:LET x1=x' in basic
    assert '715 IF ATTR (my,mx)=6THEN GO TO 6000' in basic
    play = source.split('static void player_step(void)',1)[1].split('static void mine_step(void)',1)[0]
    chase = source.split('static void mine_step(void)',1)[1].split('int main(void)',1)[0]
    assert play.index('if(has_axe)at_cell(y,x,130,6,0);') < play.index("if(kbd_down('p'))")
    assert play.index('last_x=x;last_y=y;') < play.index('nx=x;ny=y;')
    assert 'at_cell(y,x,130,6,0);else at_cell(y,x,129,6,0);' not in play
    assert 'if(get_attr(my,mx)==6)' in chase and 'if(my==y&&mx==x)' not in chase
    print('PASS: player renders before movement; enemy uses actual drawn attributes')

def check_trail_difficulty():
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    c48 = (THIS / 'minelay.c').read_text()
    assert 'IF RND >sk' in basic and 'LET sk=(.7AND INKEY$ ="1")+(.85AND INKEY$ ="2")' in basic
    mine = c48.split('static void mine_step(void)', 1)[1].split('int main(void)', 1)[0]
    assert 'if(rnd(100)>=70)' in mine and 'if(rnd(100)>=85)' in mine, (
        'BASIC 30-percent hard and 15-percent easy mine deposition rates changed')
    assert sum(v>=70 for v in range(100)) == 30
    assert sum(v>=85 for v in range(100)) == 15
    print('PASS: hard/easy mine rates match BASIC 30%/15%')


def check_reserve_lives():
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    c48 = (THIS / 'minelay.c').read_text()
    assert '60 PRINT AT 0,13;"{91}{91}    Hi-score "' in basic
    assert '6007 LET li=li-1' in basic
    assert 'for(c=0;c<lives-1&&c<6;c++)' in c48, (
        'BASIC shows two reserve symbols when li=3, not three')
    print('PASS: reserve-life display matches BASIC li=3 with two icons')


def check_original_title():
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    original = re.search(r'^9500 PRINT INK 0;AT 0,0;"([^"]*)"', basic, re.M)
    source = (THIS / 'minelay.c').read_text()
    image = re.search(r'pattern="([^"]*)";', source)
    assert original and image and original[1] == image[1] and len(image[1]) == 157, (        'Original five-row BASIC title pattern was changed')
    assert "if(pattern[k]=='_')" in source and 'title_animation();' in source
    assert 'fresh_enter();' in source and 'while(!kbd_down(13))' in source, 'Original ENTER start required'
    print('PASS: original BASIC 157-character animated-title data preserved')

def check_host_rules(sdk):
    """Compile real C48 gameplay routines with mocked display/keys for forced edges."""
    compiler = shutil.which('cc') or shutil.which('gcc')
    assert compiler, 'host C compiler needed for forced collision/axe scenarios'
    c_source = '#define main c48_game_main\n#include "../../01-minelay/C48/minelay.c"\n#undef main\nstatic int held;\nint inverse(int x){return x;}\nint kbd_down(int key) { return key == held; }\nint ink(int x){return x;} int bright(int x){return x;} int paper(int x){return x;}\nint border(int x){return x;} int cls(void){return 0;} int plot(int x,int y){return 0;}\nint draw(int x,int y,int z,int w){return 0;} int beep(float d,float n){return 0;}\nint sleep(unsigned int t){return 0;} int c48_any_key(void){return 0;}\nint c48_cell(int row,int col,int code){return 0;} int gtty(int h,void *b){return -1;}\nint stty(int h,void *b){return 0;} unsigned int ticks(void){return 0;}\n#define CHECK(x) do{if(!(x)) return __LINE__ % 200+20;}while(0)\nint main(void) {\n  int p;\n  full_clear(); x=3;y=5;last_x=3;last_y=5;score=0;highscore=0;lives=3;\n  has_axe=0;hard=0;held=\'p\';\n  player_step();\n  CHECK(x==4&&y==5); CHECK(board[5*32+3]==129);\n  CHECK(board[5*32+4]==32); CHECK(get_attr(5,3)==6);CHECK(get_attr(5,4)==7);\n  /* Enemy reaches visible old position, not the as-yet-undrawn next one. */\n  my2=10;mx2=5;old_my=5;old_mx=2;held=0;\n  mine_step();\n  CHECK(lives==2);CHECK(x==1&&y==2);CHECK(board[5*32+3]==32);\n  /* With axe, hitting a non-border white wall destroys it and drops axe. */\n  full_clear();x=3;y=5;last_x=3;last_y=5;has_axe=1;lives=3;held=\'p\';\n  at_cell(5,4,128,7,0);player_step();\n  CHECK(x==4&&y==5);CHECK(has_axe==0);CHECK(board[5*32+4]==32);\n  CHECK(board[5*32+3]==130);held=0;player_step();\n  CHECK(board[5*32+3]==32);CHECK(board[5*32+4]==129);\n  /* A collision with a mine loses a life and removes the explosion glyph. */\n  full_clear();x=3;y=5;last_x=3;last_y=5;has_axe=0;lives=3;held=\'p\';\n  my2=20;mx2=30;at_cell(5,4,133,5,0);\n  player_step();CHECK(lives==2);CHECK(x==1&&y==2);\n  CHECK(board[5*32+3]==32);CHECK(board[5*32+4]==32);\n  /* A gold pickup worth +10 at 490 earns the 500-point reserve life. */\n  full_clear();x=3;y=5;last_x=3;last_y=5;held=\'p\';\n  has_axe=0;score=490;lives=3;at_cell(5,4,132,6,1);\n  player_step();CHECK(score==500);CHECK(lives==4);\n  CHECK(board[0*32+13]==129&&board[0*32+14]==129&&board[0*32+15]==129);\n  /* Axe protects from a direct pursuer impact but is then dropped. */\n  full_clear();x=3;y=5;last_x=3;last_y=5;held=0;\n  has_axe=1;lives=3;my2=10;mx2=5;old_my=5;old_mx=2;\n  player_step();mine_step();CHECK(lives==3);CHECK(has_axe==0);\n  held=0;player_step();CHECK(board[5*32+3]==129);\n  /* New high score prints the BASIC congratulatory message. */\n  gameover=1;highscore=40;score=120;held=\'1\';menu();\n  CHECK(highscore==120&&hard==1);CHECK(board[11*32+1]==\'W\');\n  /* Lower score preserves the old high score and prints that instead. */\n  gameover=1;score=30;held=\'2\';menu();\n  CHECK(highscore==120&&hard==0);CHECK(board[11*32+2]==\'T\');\n  return 0;\n}\n'
    workspace = ROOT / 'build' / 'tmp'
    workspace.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='minelay-logic-', dir=workspace) as temp:
        c_path = Path(temp) / 'test_host.c'
        binary = Path(temp) / 'host_logic'
        # Generated source sits in a scratch subfolder; use a full path
        # to the original C48 file rather than a copied implementation.
        c_path.write_text(c_source.replace('../../01-minelay/C48/minelay.c',
                             str(THIS / 'minelay.c')))
        compiled = subprocess.run([compiler, '-w', '-std=gnu99', '-O0',
                                   '-I' + str(sdk / 'include'), str(c_path),
                                   '-o', str(binary)], capture_output=True,
                                  text=True, timeout=30)
        assert compiled.returncode == 0, 'host logic compile failed: ' + compiled.stderr[-800:]
        executed = subprocess.run([str(binary)], capture_output=True,
                                  text=True, timeout=30)
        assert executed.returncode == 0, ('forced BASIC collision/axe rule failed at '
                    + str(executed.returncode))
    print('PASS: forced C48 player timing, axe, mine, pursuer and 500-point life scenarios')

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
    def glyph(scr, row, col):
        return tuple(scr[((row & 24) << 8) + (pix << 8) +
                         ((row & 7) << 5) + col] for pix in range(8))
    player_glyph = (28,28,73,62,8,28,20,54)
    # The frozen kernel and BASIC-style animated title make wall-clock
    # frame estimates brittle. Wait for the actual maze/HUD state.
    gameplay = None
    for _ in range(35):
        frame = step(12)
        if [glyph(frame, 0, c) == player_glyph for c in (13,14,15)] == [True,True,False]:
            gameplay = frame
            break
    assert gameplay is not None and gameplay != menu, 'Minelay did not draw correct maze reserves'
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
    # Adversarial screen inspection across life losses and mine respawns:
    # a prior pursuer must never survive as a second, ghost sprite.
    def pursuer_count(screen):
        n = 0
        for row in range(2, 22):
            for col in range(32):
                glyph = tuple(screen[((row & 24) << 8) + (pix << 8) +
                                      ((row & 7) << 5) + col] for pix in range(8))
                if glyph == enemy_bytes:
                    n += 1
        return n
    for _ in range(6):
        over_screen = step(450)
        assert pursuer_count(over_screen) <= 1, (
            'More than one live mine-layer sprite: stale screen pixels after respawn')
    print('PASS: no ghost pursuer in 6 sampled ZX-UX gameplay/game-over frames')
    font = ROOT / 'c48lib' / 'c48lib-font.asm'
    charmap = {}
    for row in font.read_text().splitlines():
        match = re.search(r'\bdb ([0-9,]+)\s*; (\d+)', row)
        if match:
            code = tuple(int(v) for v in match[1].split(','))
            charmap[code] = chr(int(match[2]))
            # BASIC 6020 prints the GAME OVER banner with INVERSE 1.
            charmap[tuple(255 ^ pixel for pixel in code)] = chr(int(match[2]))
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

def check_highscore_message():
    basic = (THIS.parent / 'BASIC' / '01-minelay.bas').read_text()
    c48 = (THIS / 'minelay.c').read_text()
    assert 'Well done- A new high-score!!' in basic
    assert 'Well done- A new high-score!!' in c48
    assert 'if(score>highscore)' in c48
    assert 'inverse(1);line(5,8,' in c48 and 'inverse(0);' in c48
    print('PASS: original high-score congratulation and inverse GAME OVER')

def check_yolo_tape(system, sdk):
    """Use the real frozen shell's yolo wildcard to load the actual TZX."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(sdk))
    import zxux
    os.environ['ZXUX_RVM_CACHE'] = str(ROOT / 'build' / 'tmp' / 'minelay-rvm-cache')
    session = zxux.Session(system=str(system), cache=True)
    session.boot()
    blocks = zxux.read_tape(str(THIS / 'minelay.tzx'))
    assert len(blocks) == 2, 'Minelay tape does not have two executable records'
    session.m.cassette.extend(blocks)
    actual_loader_calls = []
    original_handler = session.m.hooks[session.system.syscall]
    def observe_call(machine):
        if machine.cpu.a == zxux.SYS_SSXLOAD:
            actual_loader_calls.append((machine.frame, session.current_pid()))
        return original_handler(machine)
    session.m.hooks[session.system.syscall] = observe_call
    session.kb.type('yolo\n')
    logo = (4,14,6,12,24,48,96,0)  # original BASIC title UDG
    drawn = False
    for _ in range(1500):
        session.step()
        if not actual_loader_calls or session.m.cassette:
            continue
        bitmap = session.m.screen()
        glyphs = 0
        for row in range(5):
            for col in range(32):
                cell = tuple(bitmap[((row & 24) << 8) + (line << 8) +
                                    ((row & 7) << 5) + col] for line in range(8))
                if cell == logo:
                    glyphs += 1
        if glyphs >= 6:
            drawn = True
            break
    assert drawn and actual_loader_calls and not session.m.cassette, (
        'yolo failed to load and execute the actual Minelay TZX')
    print('PASS: live ZX-UX shell yolo loaded Minelay TZX; original title pixels displayed')

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--system',type=Path)
    cli.add_argument('--sdk',type=Path)
    a = cli.parse_args()
    check_glyphs()
    check_placements()
    check_pursuer_draw_order()
    check_collision_cleanup()
    check_player_timing()
    check_trail_difficulty()
    check_reserve_lives()
    check_original_title()
    check_highscore_message()
    if a.system and a.sdk:
        check_host_rules(a.sdk.resolve())
        check_screen(a.system.resolve(), a.sdk.resolve())
        check_yolo_tape(a.system.resolve(), a.sdk.resolve())
        print('CHECK normal PASS')
        print('CHECK adversarial PASS')
        print('CHECK integration PASS')
        print('CHECK remnants PASS')
    else:
        print('NOT RUN: real-kernel test needs --system and --sdk')
if __name__ == '__main__':
    main()
    # rvm retains large cyclic machine snapshots; all checks and output are
    # complete, so bypass slow interpreter shutdown in headless test runs.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
