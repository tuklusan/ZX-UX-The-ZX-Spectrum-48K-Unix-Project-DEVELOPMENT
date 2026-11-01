#!/usr/bin/env python3
"""ZX-UX validation description.



"""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections'
RBC = ROOT / 'src/zx-ux-sdk/bin/rbc'
COLLECTIONS = {'Granada-Publishing': 24, 'numerical-analysis': 20,
               'www.thespectrumshow.net': 73}


def compile_one(item):
    collection, game = item
    inputs = sorted((game / 'BASIC').glob('*.bas'))
    # The graphics loader is not the full Dungeon program.
    if game.name == '43-dungeonfix-DungeonFinal-02':
        inputs = [p for p in inputs if p.name == 'DUNGEON.bas']
    outputs = []
    with tempfile.TemporaryDirectory(prefix='zxux-rbc-') as temp:
        for source in inputs:
            target = Path(temp) / 'native.ssx'
            args = [sys.executable, '-B', str(RBC), str(source), '-o', str(target)]
            try:
                run = subprocess.run(args, capture_output=True, text=True, timeout=180)
                output = (run.stderr + '\n' + run.stdout).strip()
                line = next((s for s in output.splitlines() if 'RBC_NATIVE_BLOCKED' in s), '')
                failure = re.search(r'RBC_NATIVE_BLOCKED\s+([\w.]+)', line)
                code = failure.group(1).strip(':') if failure else 'CompilationFailure'
                if run.returncode == 0 and target.is_file():
                    data = target.read_bytes()
                    if data[:4] != b'SSX1':
                        outputs.append((source.name, 'InvalidSSX'))
                        continue
                    tape = source.with_suffix('.tzx')
                    if tape.is_file():
                        target2 = Path(temp) / 'dual.ssx'
                        dual = subprocess.run([sys.executable, '-B', str(RBC), str(tape), '-o', str(target2)],
                                              capture_output=True, text=True, timeout=180)
                        if dual.returncode != 0 or not target2.is_file() or target2.read_bytes() != data:
                            outputs.append((source.name, 'IndependentTapeMismatch'))
                            continue
                    return (collection, game, data, source.name, outputs)
                outputs.append((source.name, code))
            except subprocess.TimeoutExpired:
                outputs.append((source.name, 'CompilerTimeout'))
    return (collection, game, None, '', outputs)


def main():
    games = []
    for collection, count in COLLECTIONS.items():
        directory = ARCHIVE / collection
        if directory.is_symlink() or not directory.is_dir():
            raise RuntimeError('missing original collection: ' + collection)
        found = sorted(p for p in directory.iterdir() if p.is_dir() and
                       not p.is_symlink() and re.fullmatch(r'\d{2}-.+', p.name))
        if len(found) != count:
            raise RuntimeError(f'{collection}: expected {count} programs, found {len(found)}')
        games.extend((collection, p) for p in found)
    accepted = {name: 0 for name in COLLECTIONS}
    refused = {name: 0 for name in COLLECTIONS}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for collection, game, ssx, selected, failures in pool.map(compile_one, games):
            directory = game / 'bin'
            if directory.exists() and (directory.is_symlink() or any(directory.iterdir())):
                raise RuntimeError('existing RBC result must not be overwritten: ' + str(directory))
            directory.mkdir(exist_ok=True)
            if ssx is not None:
                (directory / (game.name + '.ssx')).write_bytes(ssx)
                accepted[collection] += 1
                print('ACCEPT', collection, game.name, selected, flush=True)
            else:
                (directory / 'README.md').write_text(
                    '# ' + game.name + ' — RBC refused\n\n'
                    'Original BASIC material remains unchanged.\n'
                    'No native SSX or TZX executable is published.\n',
                    encoding='utf-8')
                refused[collection] += 1
                print('REFUSED', collection, game.name, failures, flush=True)
    print('RBC results: ' + json.dumps({'accepted': accepted, 'refused': refused}, sort_keys=True))
    if sum(accepted.values()) + sum(refused.values()) != sum(COLLECTIONS.values()):
        raise RuntimeError('incomplete RBC classification')


if __name__ == '__main__':
    main()
