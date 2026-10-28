#!/usr/bin/env python3
"""Run the unchanged 34-game ZX-UX screen/input gate in bounded parallel jobs.

Each game uses the authoritative native_gameplay_34.py two-run check, with
independent emulator boots and the same per-game frame limits. No shortcut,
file edits, alternate emulator, or claim of completed gameplay. Timed-out
and unclear runs fail closed. Results are printed, not stored as a ledger.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
import subprocess
import sys

from native_gameplay_34 import FROZEN, GAMES, SCRIPTS, SYSTEM

GATE = Path(__file__).resolve().with_name('native_gameplay_34.py')
ROOT = GATE.parents[3]
MARKER = re.compile(r'^([a-z0-9-]+): (DISPLAY CHANGED|INPUT EFFECT UNVERIFIED) '
                    r'\[(frames|exit|input)/(frames|exit|input)\]$', re.M)


def classify(game: str, code: int, stdout: str, stderr: str) -> str:
    """Never infer a pass from a partial result or an incomplete subprocess."""
    matches = MARKER.findall(stdout)
    if len(matches) != 1 or matches[0][0] != game:
        return 'ERROR: missing or ambiguous native screen result'
    changed = matches[0][1] == 'DISPLAY CHANGED'
    if changed and code == 0 and '1 display changes; 0 input effects not proven' in stdout:
        return 'DISPLAY CHANGED (not full gameplay proof)'
    if (not changed and code == 1 and
            '0 display changes; 1 input effects not proven' in stdout):
        return 'SCREEN UNCHANGED (input effect unverified)'
    return 'ERROR: gate result/exit status disagree'


def run_one(game: str, deadline: int) -> tuple[str, str]:
    command = (sys.executable, '-B', str(GATE), game)
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                text=True, timeout=deadline, check=False)
    except subprocess.TimeoutExpired:
        return game, 'TIMEOUT (unverified)'
    except OSError as exc:
        return game, 'ERROR: process failed: ' + type(exc).__name__
    status = classify(game, result.returncode, result.stdout, result.stderr)
    if status.startswith('ERROR') and result.stderr:
        status += ' (' + result.stderr.strip().splitlines()[-1][:160] + ')'
    return game, status


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=180,
                        help='wall-clock seconds per independently checked game')
    parser.add_argument('games', nargs='*', help='optional exact published game names')
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 5 or not 30 <= args.timeout <= 900:
        parser.error('jobs must be 1..5 and timeout 30..900 seconds')
    if SYSTEM.read_bytes() != FROZEN.read_bytes():
        raise RuntimeError('rebuilt ZX-UX system differs from frozen release')
    available = sorted({p.parent.parent.name for p in GAMES.glob('*/bin/*.ssx')})
    if len(available) != 34 or set(available) != set(SCRIPTS):
        raise RuntimeError('published SSX/game input set differs from checked 34')
    if args.games and (len(args.games) != len(set(args.games)) or
                       set(args.games) - set(available)):
        parser.error('unknown or duplicate game name')
    selected = sorted(args.games) if args.games else available
    results = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        tasks = {pool.submit(run_one, game, args.timeout): game
                 for game in selected}
        for task in as_completed(tasks):
            game = tasks[task]
            try:
                name, result = task.result()
                if name != game:
                    raise ValueError('game identity mismatch')
                results[game] = result
            except Exception as exc:
                results[game] = 'ERROR: ' + type(exc).__name__
            print(f'{game}: {results[game]}', flush=True)
    changed = [g for g in selected if results[g].startswith('DISPLAY CHANGED')]
    unchanged = [g for g in selected if results[g].startswith('SCREEN UNCHANGED')]
    blocked = [g for g in selected if g not in changed and g not in unchanged]
    print(f'REAL ZX-UX: {len(selected)}/34 checked; {len(changed)} changed; '
          f'{len(unchanged)} unchanged; {len(blocked)} errors/timeouts', flush=True)
    if unchanged:
        print('SCREEN UNCHANGED: ' + ', '.join(unchanged), flush=True)
    if blocked:
        print('ERROR/TIMEOUT: ' + ', '.join(blocked), flush=True)
    print('SCREEN DIFFERENCES DO NOT PROVE COMPLETE GAMEPLAY', flush=True)
    return 0 if len(selected) == 34 and not unchanged and not blocked else 1


if __name__ == '__main__':
    raise SystemExit(main())
