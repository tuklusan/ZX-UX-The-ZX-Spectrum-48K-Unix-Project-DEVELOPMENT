#!/usr/bin/env python3
"""Keep only BASIC releases with both native emulator captures."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
ARCHIVE = ROOT / 'src/assets/basic-src/original-sinclair-basic-collections'
sys.path.insert(0, str(ROOT / 'build/tools'))
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk/tools'))
from basic_portfolio import cases, write_gallery
import basicpack


def failures(log: Path, engine: str):
    pattern = re.compile(r'^RBC ' + engine + r' FAIL:?\s+(\S+)\s+(.+)$', re.M)
    rows = pattern.findall(log.read_text(encoding='utf-8'))
    names = []
    for name, message in rows:
        if 'no changed native screen after recorded input' not in message and \
                'recorded input produced no changed native screen' not in message:
            raise RuntimeError('Unreviewed capture failure: ' + engine + ' ' + name)
        names.append(name)
    if len(set(names)) != len(names):
        raise RuntimeError('Duplicate capture failure: ' + engine)
    return set(names)


def missing_from_baseline(path: Path, removed: set[tuple[str, str]]):
    result = []
    for line in path.read_text().splitlines():
        _, _, filename = line.partition('\t')
        parts = Path(filename).parts
        for collection, game in removed:
            is_binary = (len(parts) == 6 and parts[:3] ==
                         ('dist', 'assets', 'rbc-bin') and parts[3] == collection
                         and parts[4] in ('ssx', 'tzx') and
                         parts[5] in (game + '.ssx', game + '.tzx'))
            is_source = (len(parts) >= 6 and parts[:3] in
                         (('dist', 'assets', 'rbc-src'),
                          ('dist', 'assets', 'basic-src')) and
                         parts[3:5] == (collection, game))
            is_original_screen = (len(parts) >= 6 and parts[:3] ==
                                  ('dist', 'screenshots', 'basic-original') and
                                  parts[3:5] == (collection, game))
            is_screen = (len(parts) == 6 and parts[:3] ==
                         ('dist', 'screenshots', 'rbc-bin') and
                         parts[3] in ('rvm', 'fuse') and parts[4] == collection
                         and parts[5] == game + '.png')
            if is_binary or is_source or is_original_screen or is_screen:
                result.append(filename)
                break
    return sorted(set(result))


def finish(logdir: Path):
    found = list(cases())
    by_name: dict[str, list[tuple[str, str]]] = {}
    for collection, ssx, _ in found:
        by_name.setdefault(ssx.stem, []).append((collection, ssx.stem))
    missing = {}
    failed = {}
    for engine, tag in (('rvm', 'RVM'), ('fuse', 'Fuse')):
        missing[engine] = {(collection, ssx.stem) for collection, ssx, _ in found
                           if not (DIST / 'screenshots/rbc' / engine / collection /
                                   (ssx.stem + '.png')).is_file()}
        names = failures(logdir / ('rbc-' + engine + '.log'), tag)
        matched = set()
        for name in names:
            if len(by_name.get(name, ())) != 1:
                raise RuntimeError('Missing or ambiguous failed BASIC case: ' + name)
            matched.add(by_name[name][0])
        failed[engine] = matched
        if matched != missing[engine]:
            raise RuntimeError('Capture failures and missing screenshots differ: ' + engine)
    refused = missing['rvm'] | missing['fuse']
    counts = Counter(collection for collection, _ in refused)
    # Only the two collections with witnessed failures can lose a release.
    if len(refused) > 5 or counts.get('Granada-Publishing', 0) > 3 or \
            counts.get('www.thespectrumshow.net', 0) > 2 or \
            set(counts) - {'Granada-Publishing', 'www.thespectrumshow.net'}:
        raise RuntimeError('Unexpected capture loss; existing releases retained')
    if refused:
        for collection, game in sorted(refused):
            directory = ARCHIVE / collection / game / 'bin'
            executable = directory / (game + '.ssx')
            if not executable.is_file():
                raise RuntimeError('Missing compiled result: ' + str(executable))
            executable.unlink()
            (directory / (game + '.source')).unlink(missing_ok=True)
            (directory / 'README.md').write_text(
                '# RBC refused\n\nNative RVM and Fuse capture pair was not verified.\n',
                encoding='utf-8')
            for engine in ('rvm', 'fuse'):
                (DIST / 'screenshots/rbc' / engine / collection /
                 (game + '.png')).unlink(missing_ok=True)
        # Rebuild only the affected BASIC distribution paths. Archive inputs stay intact.
        for collection in sorted(counts):
            for category in ('rbc-bin', 'rbc-src', 'basic-src'):
                shutil.rmtree(DIST / 'assets' / category / collection,
                              ignore_errors=True)
            shutil.rmtree(DIST / 'screenshots/basic-original' / collection,
                          ignore_errors=True)
        basicpack.package(ROOT / 'src', DIST)
        for engine, title in (('rvm', 'RVM'), ('fuse', 'Fuse')):
            write_gallery(DIST / 'screenshots/rbc' / engine, title)
    omissions = missing_from_baseline(logdir / 'baseline.tree', refused)
    (logdir / 'capture-omissions.txt').write_text(
        ''.join(name + '\n' for name in omissions), encoding='utf-8')
    (logdir / 'capture-exits.txt').write_text(
        ''.join('rbc-' + engine + '\n' for engine in ('rvm', 'fuse')
                if failed[engine]), encoding='utf-8')
    print('BASIC native captures: included', len(found) - len(refused),
          'refused', len(refused), flush=True)
    for collection, game in sorted(refused):
        print('REFUSED', collection, game, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', type=Path)
    options = parser.parse_args()
    finish(options.logs)


if __name__ == '__main__':
    main()
