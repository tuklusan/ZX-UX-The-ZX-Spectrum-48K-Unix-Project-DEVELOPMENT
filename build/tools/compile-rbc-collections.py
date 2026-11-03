#!/usr/bin/env python3
"""Reconsider refused RBC programs while retaining accepted native binaries."""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections'
RBC = ROOT / 'src/zx-ux-sdk/bin/rbc'
COLLECTIONS = {'Granada-Publishing': 24, 'numerical-analysis': 20,
               'www.thespectrumshow.net': 73}
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rtap


def checked_ssx(data: bytes) -> bool:
    try:
        rld.parse_ssx(data)
        return max(len(data), rtap.need(data)) <= 14000
    except (ValueError, IndexError, KeyError):
        return False


def matching_tapes(source: Path, tapes: list[Path]) -> list[Path]:
    """Associate original tapes by source stem, including derived recordings."""
    stem = source.stem.casefold()
    return [p for p in tapes if p.stem.casefold() == stem or
            p.stem.casefold().startswith(stem + '-')]


def compile_one(item):
    collection, game = item
    directory = game / 'bin'
    executable = directory / (game.name + '.ssx')
    reason = directory / 'README.md'
    marker = directory / (game.name + '.source')
    if directory.is_symlink() or any(p.is_symlink() for p in (executable, reason, marker)):
        raise RuntimeError('unsafe native result: ' + str(game))
    if executable.is_file():
        if reason.exists() or not checked_ssx(executable.read_bytes()):
            raise RuntimeError('invalid previously accepted binary: ' + str(executable))
        return collection, game, None, None, ('preserved',)
    if directory.is_dir() and any(p for p in directory.iterdir() if p != reason):
        raise RuntimeError('unrecognized native result: ' + str(directory))
    folder = game / 'BASIC'
    sources = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.casefold() == '.bas')
    tapes = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.casefold() == '.tzx')
    if any(p.is_symlink() for p in sources + tapes):
        raise RuntimeError('linked original input: ' + str(folder))
    failures = []
    passed = []
    with tempfile.TemporaryDirectory(prefix='zxux-rbc-') as temp:
        work = Path(temp)
        for index, source in enumerate(sources):
            pair = matching_tapes(source, tapes)
            if len(sources) > 1 and not pair:
                failures.append((source.name, 'UnmatchedBASICVariant'))
                continue
            target = work / f'{index}.ssx'
            try:
                run = subprocess.run([sys.executable, '-B', str(RBC), str(source),
                                      '-o', str(target)], capture_output=True,
                                     text=True, timeout=180)
                if run.returncode or not target.is_file():
                    found = re.search(r'RBC_NATIVE_BLOCKED\s+([\w.]+)',
                                      run.stderr + run.stdout)
                    failures.append((source.name, found.group(1) if found else 'CompileFailure'))
                    continue
                data = target.read_bytes()
                if not checked_ssx(data):
                    failures.append((source.name, 'InvalidOrOversizedSSX'))
                    continue
                verified = True
                for n, tape in enumerate(pair):
                    # The RBC tape verifier requires the original BAS to have
                    # the same stem as its tape. Rename copies, never originals.
                    tape_dir = work / f'tape-{index}-{n}'
                    tape_dir.mkdir()
                    (tape_dir / (tape.stem + '.bas')).write_bytes(source.read_bytes())
                    linked_tape = tape_dir / (tape.stem + '.tzx')
                    linked_tape.write_bytes(tape.read_bytes())
                    dual = tape_dir / 'verified.ssx'
                    check = subprocess.run([sys.executable, '-B', str(RBC),
                                            str(linked_tape), '-o', str(dual)],
                                           capture_output=True, text=True, timeout=180)
                    if check.returncode or not dual.is_file() or not checked_ssx(dual.read_bytes()):
                        failures.append((source.name, 'IndependentTapeMismatch:' + tape.name))
                        verified = False
                        break
                if verified:
                    passed.append((source.name, data))
            except subprocess.TimeoutExpired:
                failures.append((source.name, 'CompilerTimeout'))
    if len(passed) != 1:
        if len(passed) > 1:
            failures.append(('*', 'AmbiguousCompiledVariants'))
        return collection, game, None, None, tuple(failures)
    return collection, game, passed[0][1], passed[0][0], tuple(failures)


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
    new = {name: 0 for name in COLLECTIONS}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for collection, game, ssx, selected, details in pool.map(compile_one, games):
            directory = game / 'bin'
            if details == ('preserved',):
                accepted[collection] += 1
                continue
            if ssx is None:
                refused[collection] += 1
                if not (directory / 'README.md').is_file():
                    directory.mkdir(exist_ok=True)
                    (directory / 'README.md').write_text(
                        '# RBC refused\n\nNo verified native executable was produced.\n',
                        encoding='utf-8')
                print('REFUSED', collection, game.name, details, flush=True)
                continue
            directory.mkdir(exist_ok=True)
            target = directory / (game.name + '.ssx')
            if target.exists() or not checked_ssx(ssx):
                raise RuntimeError('unsafe native result: ' + str(target))
            target.write_bytes(ssx)
            if len(list((game / 'BASIC').glob('*.bas'))) > 1:
                (directory / (game.name + '.source')).write_text(selected + '\n', encoding='utf-8')
            (directory / 'README.md').unlink(missing_ok=True)
            accepted[collection] += 1
            new[collection] += 1
            print('ACCEPT', collection, game.name, selected, flush=True)
    print('RBC results:', json.dumps({'accepted': accepted, 'refused': refused,
                                      'new': new}, sort_keys=True))
    if sum(accepted.values()) + sum(refused.values()) != sum(COLLECTIONS.values()):
        raise RuntimeError('incomplete RBC classification')


if __name__ == '__main__':
    main()
