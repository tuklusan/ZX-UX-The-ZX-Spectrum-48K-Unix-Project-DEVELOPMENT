#!/usr/bin/env python3
"""Bounded 34-game emulator screen gate with six independent default INPUT pairs.

The published SSX remains untouched by the runner; six independently built
BAS/TZX candidates are linked into an isolated untracked test shadow.
Each game boots twice in the real ZX-UX Z80 loader. Five minutes per game
and 120 minutes per runner are ceilings. A screen change is not gameplay proof.
No original BAS/TZX, system tape, ROM or published executable is overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import os
import subprocess
import time
import sys

ROOT = Path(__file__).resolve().parents[3]
TESTS = Path(__file__).resolve().parent
GAME_ROOT = ROOT / 'src/bonus/60-programs'
TEMP = ROOT / 'build/tmp'
SHADOW = TEMP / 'rbc-input-shadow'
PAIRS = TEMP / 'rbc-input-six-pairs'
SIX = frozenset(('01-minelay', '07-critical-path-analysis',
    '23-biorhythms', '30-space-traffic', '39-flying-geese', '56-roots'))


def verify_candidate_pair(name: str):
    """Refuse stale or overwritten --prepared candidates before live testing."""
    directory = PAIRS / name
    blobs = []
    for side in ('bas', 'tzx'):
        candidate = directory / ('from-' + side + '.ssx')
        outcome = directory / (side + '-outcome.json')
        report_path = directory / (side + '-report.json')
        if not all(x.is_file() for x in (candidate, outcome, report_path)):
            raise ValueError(name + ': independent candidate/proof missing: ' + side)
        data = candidate.read_bytes()
        result = json.loads(outcome.read_text())
        report = json.loads(report_path.read_text())
        if (result.get('exit') != 0 or result.get('size') != len(data) or
                result.get('sha256') != hashlib.sha256(data).hexdigest() or
                report.get('native_linker') != 'ras/rld' or
                not report.get('native_three_base_source_verified') or
                not report.get('input_source_bridge_three_base_verified') or
                report.get('optimizer_used') or report.get('file') != len(data) or
                not isinstance(report.get('total'), int) or
                max(report['total'], len(data)) > 14000):
            raise ValueError(name + ': independent candidate/proof invalid: ' + side)
        blobs.append(data)
    if blobs[0] != blobs[1]:
        raise ValueError(name + ': independently compiled BAS/TZX SSX disagree')
    return directory / 'from-bas.ssx'


def prepare_shadow():
    games = sorted(GAME_ROOT.glob('*/bin/*.ssx'))
    if len(games) != 34 or len({p.parent.parent.name for p in games}) != 34:
        raise ValueError('published 34-game SSX set changed')
    for original in games:
        folder = original.parents[1]
        dest = SHADOW / folder.name
        (dest / 'bin').mkdir(parents=True, exist_ok=True)
        if folder.name in SIX:
            source = verify_candidate_pair(folder.name)
        else:
            source = original
        for link, target in ((dest / 'BASIC', folder / 'BASIC'),
                             (dest / 'bin' / original.name, source)):
            if link.is_symlink():
                link.unlink()
            elif link.exists():
                raise ValueError('shadow contains unexpected ordinary file: ' + str(link))
            link.symlink_to(target.resolve())
    if len(list(SHADOW.glob('*/bin/*.ssx'))) != 34:
        raise ValueError('candidate shadow input set changed')


def real_one(name):
    sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(TESTS)]
    import native_gameplay_34 as gate
    from test_native_input_original_games import CASES as dates
    from test_native_input_two_game_progression import CASES as progression
    gate.GAMES = SHADOW
    gate.SCRIPTS = dict(gate.SCRIPTS)
    for game, keys, *_ in dates:
        gate.SCRIPTS[game] = keys
    for game, keys, *_ in progression:
        gate.SCRIPTS[game] = keys
    gate.SCRIPTS['07-critical-path-analysis'] = (
        '{WAIT 200}{ENTER}{WAIT 200}{ENTER}{WAIT 200}{ENTER}'
        '{WAIT 100}1{ENTER}{WAIT 100}0{ENTER}{WAIT 100}12{ENTER}')
    baseline = gate.capture
    def adjusted(game, script, frames):
        if game.name in SIX:
            frames = max(frames, 2300)
        return baseline(game, script, frames)
    gate.capture = adjusted
    return gate.main([name])


def one_child(name: str, timeout: int, results: Path):
    cmd = [sys.executable, '-B', str(Path(__file__).resolve()), '--one', name]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=ROOT, timeout=timeout, check=False)
        code, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        code = None
        stdout = exc.stdout or b''
        stderr = exc.stderr or b''
        if isinstance(stdout, bytes):
            stdout = stdout.decode('utf-8', 'replace')
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', 'replace')
    (results / (name + '.stdout')).write_text(stdout)
    (results / (name + '.stderr')).write_text(stderr)
    (results / (name + '.exit')).write_text(str(code) + '\n')
    status = ('DISPLAY CHANGED' if code == 0 and
              f'{name}: DISPLAY CHANGED' in stdout and
              '1 display changes; 0 input effects not proven' in stdout
              else 'INPUT UNVERIFIED' if code == 1 and
              f'{name}: INPUT EFFECT UNVERIFIED' in stdout
              else 'TIMEOUT' if code is None else 'ERROR')
    return name, status


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('games', nargs='*')
    p.add_argument('--one', help=argparse.SUPPRESS)
    p.add_argument('--prepared', action='store_true',
                   help='reuse independently validated six BAS/TZX pair builds')
    p.add_argument('--jobs', type=int, default=12)
    p.add_argument('--batch-size', type=int, default=12)
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--runner-timeout', type=int, default=7200)
    args = p.parse_args(argv)
    if args.one:
        return real_one(args.one)
    if not 1 <= args.jobs <= 12 or not 1 <= args.batch_size <= 12:
        p.error('jobs and batch-size must be 1..12')
    if not 30 <= args.timeout <= 300:
        p.error('per-game timeout must be 30..300 seconds')
    if not 300 <= args.runner_timeout <= 7200:
        p.error('runner timeout must be 300..7200 seconds')
    if not args.prepared:
        process = subprocess.run([
            sys.executable, '-B', str(TESTS / 'native_input_six_pairs.py')],
            cwd=ROOT, check=False)
        if process.returncode:
            raise RuntimeError('independent six-pair source gate failed')
    prepare_shadow()
    discovered = sorted(p.parent.parent.name for p in SHADOW.glob('*/bin/*.ssx'))
    if args.games and (len(args.games) != len(set(args.games)) or
                       set(args.games) - set(discovered)):
        raise ValueError('unknown or duplicate requested native game')
    selected = sorted(args.games or discovered)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    results = TEMP / ('rbc-input-shadow-' + stamp + '-' + str(os.getpid()))
    results.mkdir(parents=True, exist_ok=False)
    print('EMULATOR LOGS: ' + str(results), flush=True)
    statuses = {}
    started = time.monotonic()
    for index in range(0, len(selected), args.batch_size):
        group = selected[index:index+args.batch_size]
        print('BATCH ' + str(index//args.batch_size+1) + ': ' + ', '.join(group), flush=True)
        if time.monotonic()-started + args.timeout * ((len(group)+args.jobs-1)//args.jobs) > args.runner_timeout:
            raise TimeoutError('shadow runner cannot admit group within 120-minute budget')
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(group))) as pool:
            tasks = {pool.submit(one_child, name, args.timeout, results): name
                     for name in group}
            for task in as_completed(tasks):
                try:
                    name, status = task.result()
                except Exception as exc:
                    name = tasks[task]
                    status = 'ERROR: ' + type(exc).__name__ + ': ' + str(exc)
                    (results / (name+'.stderr')).write_text(status + '\n')
                statuses[name] = status
                print(f'{name}: {status}', flush=True)
    complete = sum(v == 'DISPLAY CHANGED' for v in statuses.values())
    print(f'RUNNER ELAPSED: {time.monotonic()-started:.3f}s / {args.runner_timeout}s', flush=True)
    print(f'REAL ZX-UX INPUT SHADOW: {complete}/{len(selected)} '
          'display responses; gameplay outcomes remain separate', flush=True)
    return 0 if complete == len(selected) else 1


if __name__ == '__main__':
    raise SystemExit(main())
