"""Fail-closed RBC Round 2 stages. No corpus work before all compiler gates.

The command is deliberately useful outside GitHub Actions. Every failed test,
missing suite, source change, or incomplete compile result stops its stage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

BASE = 'a464aa0ea5604aa392b5383fbc82f84d98fe96e1'
STAGES = ('val', 'sysvars', 'loops', 'fidelity', 'fonts', 'memory')
MIN_CASES = {'val': 4, 'sysvars': 4, 'loops': 4, 'fidelity': 4,
             'fonts': 4, 'memory': 3}


def source_gate(root: Path):
    changed = subprocess.run(['git', 'diff', '--name-only', BASE, 'HEAD', '--',
                              'src/bonus/60-programs', 'src/zx-ux',
                              'src/zx-ux-sdk', 'dist', 'release'], cwd=root,
                             capture_output=True, text=True, check=True).stdout.splitlines()
    unauthorized = [p for p in changed if not (
        p.startswith('src/bonus/60-programs/') and '/bin/' in p)]
    if unauthorized:
        raise RuntimeError('Protected source/release change: ' + ', '.join(unauthorized[:8]))
    games = sorted(p for p in (root / 'src/bonus/60-programs').iterdir()
                   if p.is_dir() and len(p.name) > 3 and p.name[:2].isdigit()
                   and p.name[2] == '-')
    if len(games) != 60:
        raise RuntimeError(f'Expected 60 original games, found {len(games)}')
    for game in games:
        for suffix in ('.bas', '.tzx'):
            if not (game / 'BASIC' / (game.name + suffix)).is_file():
                raise RuntimeError(f'Missing original {game.name}{suffix}')
        if (game / 'bin').exists() and any((game / 'bin').iterdir()):
            raise RuntimeError(f'Outcomes not reset: {game.name}/bin')
    tmp = root / 'build/tmp/rbc-round2'
    if tmp.exists() and any(tmp.iterdir()):
        raise RuntimeError('Old RBC runner workspace is not empty')
    return 120


def suite_gate(root: Path, stage: str):
    suite_path = root / 'experiments/hisoft-rbc-2026-10-22/tests' / ('test_round2_' + stage + '.py')
    if not suite_path.is_file():
        raise RuntimeError(f'{stage}: missing mandatory executable test suite')
    suite = unittest.defaultTestLoader.discover(str(suite_path.parent), pattern=suite_path.name)
    count = suite.countTestCases()
    if count < MIN_CASES[stage]:
        raise RuntimeError(f'{stage}: only {count} tests, requires {MIN_CASES[stage]}')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.testsRun != count:
        raise RuntimeError(f'{stage}: failed required tests')
    return count


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_gate(root: Path):
    work = root / 'build/tmp/rbc-round2'
    path = work / 'results.json'
    if not path.is_file():
        raise RuntimeError('No complete 120-path compile result set')
    data = json.loads(path.read_text())
    results = data.get('results', {})
    if len(results) != 60:
        raise RuntimeError(f'Only {len(results)} of 60 comparison results exist')
    problems = []
    for game, item in sorted(results.items()):
        slot = work / game
        published = work / 'published' / game / 'bin'
        if not (slot / 'comparison.json').is_file():
            problems.append(game + ': missing separate comparison record')
            continue
        if json.loads((slot / 'comparison.json').read_text()) != item:
            problems.append(game + ': comparison changed after run')
        paths = list(published.iterdir()) if published.is_dir() else []
        if len(paths) != 1:
            problems.append(game + ': not exactly one proposed outcome')
            continue
        for side in ('bas', 'tzx'):
            r = item.get(side, {})
            required = ('exit_status', 'stderr', 'stdout', 'source', 'sha256_input', 'rbc_revision', 'native_linked')
            if any(k not in r for k in required):
                problems.append(game + f': incomplete {side} diagnostics')
            output = slot / ('from-' + side + '.ssx')
            if r.get('native_linked'):
                if not output.is_file() or sha(output) != r.get('sha256_output') or output.stat().st_size != r.get('linked_bytes'):
                    problems.append(game + f': {side} linked bytes or hash differ')
            elif output.exists():
                problems.append(game + f': {side} has unlinked output')
        a, b = item['bas'], item['tzx']
        comparison = item.get('comparison', {})
        status = comparison.get('status')
        if a.get('native_linked') and b.get('native_linked'):
            lhs, rhs = (slot / 'from-bas.ssx').read_bytes(), (slot / 'from-tzx.ssx').read_bytes()
            first = next((i for i in range(min(len(lhs), len(rhs))) if lhs[i] != rhs[i]), min(len(lhs), len(rhs)))
            if lhs == rhs:
                if status != 'identical' or paths[0].name != game + '.ssx' or paths[0].read_bytes() != lhs:
                    problems.append(game + ': matching binaries not published as BAS SSX')
            elif status != 'mismatch' or comparison.get('first_difference') != first or paths[0].name != 'README.md':
                problems.append(game + ': mismatching linked binaries improperly classified')
        elif status != 'unavailable' or paths[0].name != 'README.md':
            problems.append(game + ': failed path improperly classified')
    if problems:
        raise RuntimeError('Corpus gate failed: ' + '; '.join(problems[:15]))
    return 120, 60


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('source', *STAGES, 'corpus'))
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.stage == 'source':
        print('Source gate PASS:', source_gate(root), 'original inputs')
    elif args.stage == 'corpus':
        print('Corpus gate PASS:', corpus_gate(root))
    else:
        print(args.stage, 'gate PASS:', suite_gate(root, args.stage), 'required tests')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('RBC Round 2 gate FAILED:', exc, file=sys.stderr)
        sys.exit(1)
