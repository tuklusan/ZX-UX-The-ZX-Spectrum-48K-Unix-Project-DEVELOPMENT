#!/usr/bin/env python3
"""Bounded real-ZX-UX interaction gate for all 34 published native games.

A distinct 48K emulator boot for each paired no-input/scripted run.
Identical frame limits make screen changes observable without claiming
that every level or winning condition has been reached. Fail if not all
34 games show a screened input effect; incomplete coverage remains visible.
No simulator, fabricated screenshot, game edits or output ledger.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm

SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
GAMES = ROOT / 'src/bonus/60-programs'

# Explicit inputs chosen from original BASIC instructions/keyboard tests.
# A WAIT lets native instructions and intro screens execute before typing.
SCRIPTS = {
    '01-minelay': '{ENTER}{WAIT 140}q{WAIT 100}i',
    '03-tug-of-war': 'a',
    '06-motocross': '1{WAIT 120}a{WAIT 120}j',
    '07-critical-path-analysis': '{ENTER}{WAIT 100}1',
    '09-battleships': '6{WAIT 90}8{WAIT 60}0',
    '10-tanx': 'a{WAIT 100}z{WAIT 80}{ENTER}',
    '12-flying-bomb': 'a{WAIT 100}m{WAIT 50}k',
    '14-scuba': '{WAIT 800}x{WAIT 90}z',
    '16-snap': 'a{WAIT 120}{SPACE}',
    '17-paypackets': 'a{ENTER}',
    '18-newmarket': '3{ENTER}',
    '23-biorhythms': '1980{ENTER}{WAIT 80}10{ENTER}{WAIT 80}28{ENTER}',
    '24-aben': 'v{WAIT 100}z{WAIT 80}m',
    '25-galaxians': 'a{WAIT 100}z{WAIT 80}{ENTER}',
    '28-dam-busters': 'a{WAIT 100}z{WAIT 80}{ENTER}',
    '29-oxo': '5{WAIT 80}1{ENTER}',
    '30-space-traffic': '{ENTER}{WAIT 110}z{WAIT 90}x',
    '31-dam-eaters': 'z',
    '32-buzzy-bee': 'a{WAIT 100}z{WAIT 80}{ENTER}',
    '33-heli-bomber': 'a{WAIT 100}0',
    '35-giant-rats': 'a{WAIT 100}z{WAIT 80}{ENTER}',
    '37-xmas-eve': 'z{WAIT 90}x',
    '39-flying-geese': 'a{WAIT 90}a',
    '40-wordsum': 'a{ENTER}',
    '42-bricklayer': 'a{WAIT 120}z{WAIT 200}m',
    '43-dogfight': 'a{WAIT 100}z{WAIT 80}{ENTER}',
    '47-exocet': 'z{WAIT 90}x',
    '49-drag-racer': 'm{WAIT 70}1',
    '50-moonlander': 'a{WAIT 100}z{WAIT 80}{ENTER}',
    '54-swordsman': 'q{WAIT 100}z',
    '56-roots': '{WAIT 400}{ENTER}{WAIT 70}{ENTER}',
    '57-bulls-and-cows': '9{ENTER}{WAIT 50}1234{ENTER}',
    '59-mushroom-invasion': '1{WAIT 90}5',
    '60-countabout': 'a{WAIT 90}a',
}
LATE = frozenset(('01-minelay', '06-motocross',
                  '07-critical-path-analysis', '14-scuba',
                  '23-biorhythms', '24-aben', '30-space-traffic',
                  '54-swordsman', '56-roots'))


def capture(game: Path, script: str, frames: int):
    program = game / 'bin' / (game.name + '.ssx')
    image = program.read_bytes()
    parsed = rld.parse_ssx(image)
    total = len(parsed['image']) + parsed['bss'] + parsed['stack']
    if (max(total, len(image)) > 14000 or parsed['entry'] != 0 or
            not (game / 'BASIC' / (game.name + '.bas')).is_file() or
            not (game / 'BASIC' / (game.name + '.tzx')).is_file()):
        raise ValueError(game.name + ': invalid published game or loader size')
    runner = rvm.run_kernel(program, keys=script, frames=frames, system=SYSTEM)
    if runner.fg.started is None:
        raise ValueError(game.name + ': loader never executed the native game')
    if runner.why not in ('frames', 'exit', 'input'):
        raise ValueError(game.name + ': unexpected emulator exit: ' + runner.why)
    if runner.fg.ended is not None:
        if runner.fg.status != 0 or runner.session.owns_screen(runner.fg.pid):
            raise ValueError(game.name + ': process did not exit cleanly')
        runner.session.wait_prompt(1500)
        if runner.session.last_line() != '#':
            raise ValueError(game.name + ': shell prompt not restored')
    pic, _ = runner.picture()
    if len(pic) != 6912:
        raise ValueError(game.name + ': no real Spectrum display buffer')
    return hashlib.sha256(pic).hexdigest(), runner.why


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('games', nargs='*', help='optional exact game directory names')
    args = parser.parse_args(argv)
    if SYSTEM.read_bytes() != FROZEN.read_bytes():
        raise ValueError('rebuilt ZX-UX tape differs from original release')
    games = sorted(p.parent.parent for p in GAMES.glob('*/bin/*.ssx'))
    if (len(games) != 34 or set(SCRIPTS) != {g.name for g in games}):
        raise ValueError('34 checked SSX input set changed')
    if args.games:
        if set(args.games) - set(SCRIPTS):
            raise ValueError('unrecognized published game requested')
        games = [g for g in games if g.name in args.games]
    changed = []
    unchanged = []
    for game in games:
        frames = 1300 if game.name in LATE else 900
        control, state_a = capture(game, '', frames)
        response, state_b = capture(game, '{WAIT 300}' + SCRIPTS[game.name], frames)
        if control == response:
            unchanged.append(game.name)
            result = 'INPUT EFFECT UNVERIFIED'
        else:
            changed.append(game.name)
            result = 'DISPLAY CHANGED'
        print(f'{game.name}: {result} [{state_a}/{state_b}]', flush=True)
    print(f'LIVE ZX-UX: {len(games)} loaded; {len(changed)} display changes; '
          f'{len(unchanged)} input effects not proven', flush=True)
    if unchanged:
        print('UNRESOLVED: ' + ', '.join(unchanged), flush=True)
    # A run with an unanswered interactive game is not full gameplay proof.
    return 1 if unchanged else 0


if __name__ == '__main__':
    raise SystemExit(main())
