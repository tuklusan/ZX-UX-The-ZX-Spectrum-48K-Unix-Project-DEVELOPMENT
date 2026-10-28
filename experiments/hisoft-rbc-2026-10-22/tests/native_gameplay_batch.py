#!/usr/bin/env python3
"""Run all 34 unchanged SSX games in bounded real-ZX-UX emulator batches.

Each game runs the original two-boot native_gameplay_34.py comparison.
At most five games execute at once; each has a 40-minute default timeout.
Raw subprocess results are saved under untracked build/tmp for every game,
including failures and timeouts. A changed screen is not gameplay proof.
No game executable, BASIC original, system tape or ROM is changed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys

from native_gameplay_34 import FROZEN, GAMES, SCRIPTS, SYSTEM

GATE = Path(__file__).resolve().with_name('native_gameplay_34.py')
ROOT = GATE.parents[3]
MARKER = re.compile(r'^([a-z0-9-]+): (DISPLAY CHANGED|INPUT EFFECT UNVERIFIED) '
                    r'\[(frames|exit|input)/(frames|exit|input)\]$', re.M)
INPUT_GAMES = frozenset(('01-minelay', '07-critical-path-analysis',
                        '23-biorhythms', '30-space-traffic', '56-roots'))


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


def run_one(game: str, deadline: int) -> tuple[str, str, int | None, str, str]:
    command = (sys.executable, '-B', str(GATE), game)
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                text=True, timeout=deadline, check=False)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b''
        stderr = exc.stderr or b''
        if isinstance(stdout, bytes):
            stdout = stdout.decode('utf-8', 'replace')
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', 'replace')
        return game, 'TIMEOUT (unverified)', None, stdout, stderr
    except OSError as exc:
        return game, 'ERROR: process failed: ' + type(exc).__name__, None, '', str(exc)
    status = classify(game, result.returncode, result.stdout, result.stderr)
    if status.startswith('ERROR') and result.stderr:
        status += ' (' + result.stderr.strip().splitlines()[-1][:160] + ')'
    return game, status, result.returncode, result.stdout, result.stderr


def save_result(directory: Path, game: str, status: str, code: int | None,
                stdout: str, stderr: str) -> None:
    """Save exact stdout/stderr and exit status, including unverified cases."""
    path = directory / (game + '.log')
    if path.exists():
        raise FileExistsError(path)
    with path.open('x', encoding='utf-8') as output:
        output.write('GAME: ' + game + '\nSTATUS: ' + status + '\nEXIT: ' +
                     (str(code) if code is not None else 'UNKNOWN') +
                     '\n--- STDOUT ---\n' + stdout + '\n--- STDERR ---\n' + stderr)
        output.flush()
        os.fsync(output.fileno())


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=5)
    parser.add_argument('--batch-size', type=int, default=5,
                        help='sequential groups of at most five game subprocesses')
    parser.add_argument('--timeout', type=int, default=2400,
                        help='per-game wall-clock limit in seconds (default: 40 minutes)')
    parser.add_argument('--results-dir', type=Path,
                        default=ROOT / 'build/tmp/rbc-gameplay-34',
                        help='untracked directory for raw per-game test logs')
    parser.add_argument('games', nargs='*', help='optional exact published game names')
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 5 or not 1 <= args.batch_size <= 5:
        parser.error('jobs and batch-size must each be 1..5')
    if not 30 <= args.timeout <= 2400:
        parser.error('timeout must be 30..2400 seconds')
    if not args.results_dir.resolve().is_relative_to((ROOT / 'build/tmp').resolve()):
        parser.error('results-dir must stay under untracked build/tmp')
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    if SYSTEM.read_bytes() != FROZEN.read_bytes():
        raise RuntimeError('rebuilt ZX-UX system differs from frozen release')
    available = sorted({p.parent.parent.name for p in GAMES.glob('*/bin/*.ssx')})
    if len(available) != 34 or set(available) != set(SCRIPTS):
        raise RuntimeError('published SSX/game input set differs from checked 34')
    if args.games and (len(args.games) != len(set(args.games)) or
                       set(args.games) - set(available)):
        raise ValueError('unknown or duplicate game name')
    selected = sorted(args.games) if args.games else available
    session = args.results_dir / ('run-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') +
                                  '-' + str(os.getpid()))
    session.mkdir(parents=True, exist_ok=False)
    print('RAW GAME LOGS: ' + str(session), flush=True)
    results = {}
    for first in range(0, len(selected), args.batch_size):
        group = selected[first:first + args.batch_size]
        print(f'BATCH {first // args.batch_size + 1}: {", ".join(group)}', flush=True)
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(group))) as pool:
            tasks = {pool.submit(run_one, game, args.timeout): game for game in group}
            for task in as_completed(tasks):
                game = tasks[task]
                try:
                    name, status, code, stdout, stderr = task.result()
                    if name != game:
                        raise ValueError('game identity mismatch')
                except Exception as exc:
                    status, code, stdout, stderr = 'ERROR: ' + type(exc).__name__, None, '', str(exc)
                save_result(session, game, status, code, stdout, stderr)
                results[game] = status
                print(f'{game}: {status}', flush=True)
    changed = [g for g in selected if results[g].startswith('DISPLAY CHANGED')]
    unchanged = [g for g in selected if results[g].startswith('SCREEN UNCHANGED')]
    blocked = [g for g in selected if g not in changed and g not in unchanged]
    print(f'REAL ZX-UX: {len(results)}/{len(selected)} completed; '
          f'{len(changed)} changed; {len(unchanged)} unchanged; '
          f'{len(blocked)} errors/timeouts', flush=True)
    if unchanged:
        input_unverified = [g for g in unchanged if g in INPUT_GAMES]
        other_unverified = [g for g in unchanged if g not in INPUT_GAMES]
        if input_unverified:
            print('UNVERIFIED INPUT GAMES: ' + ', '.join(input_unverified), flush=True)
        if other_unverified:
            print('UNVERIFIED OTHER KEYBOARD GAMES: ' + ', '.join(other_unverified), flush=True)
    if blocked:
        print('ERROR/TIMEOUT: ' + ', '.join(blocked), flush=True)
    print('SCREEN DIFFERENCES DO NOT PROVE COMPLETE GAMEPLAY', flush=True)
    # Subset success means only those checked games showed a screen difference.
    return 0 if not unchanged and not blocked else 1


if __name__ == '__main__':
    raise SystemExit(main())
