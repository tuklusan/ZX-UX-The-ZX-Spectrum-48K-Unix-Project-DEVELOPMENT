#!/usr/bin/env python3
"""Copy finished ZX-UX files to release/ without wrapping them in archives.

Run the build and tests first. You may pass a folder containing test logs.
"""
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
RELEASE = ROOT / 'release'


def deliver(source: Path, name: str, required: bool = True) -> bool:
    if not source.is_file():
        if required:
            raise SystemExit(f'Missing build file: {source}')
        return False
    target = RELEASE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(f'{target.relative_to(ROOT)}  {target.stat().st_size} bytes')
    return True


def copy_matching(directory: Path, pattern: str, destination: str) -> int:
    count = 0
    for item in sorted(directory.glob(pattern)):
        if item.is_file():
            deliver(item, f'{destination}/{item.name}')
            count += 1
    return count


def main(arguments: list[str]) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    for name in ('ZX-UX.tzx', 'ZX-UX.tap', 'ZX-UX-c48.tzx',
                 'ZX-UX-multitask.z80', 'ZX-UX-multitask.png'):
        deliver(BUILD / name, name)
    deliver(BUILD / 'test.z80', 'ZX-UX.z80')
    for name in ('c48-apps.tzx', 'c48-demos.tzx', 'c48-examples.tzx',
                 'c48-games.tzx', 'c48-multitask.tzx'):
        deliver(BUILD / name, name)
    if not copy_matching(BUILD / 'c48', '*.tap', 'c48'):
        raise SystemExit('Missing program tapes')
    if not copy_matching(BUILD / 'c48', '*.ssx', 'c48'):
        raise SystemExit('Missing compiled programs')
    deliver(BUILD / 'gallery.html', 'gallery.html')
    deliver(BUILD / 'sizes.json', 'sizes.json', required=False)
    copy_matching(BUILD / 'shots', '*.png', 'screens/system')
    copy_matching(BUILD / 'shots-vm', '*.png', 'screens/vm')
    if arguments:
        logs = Path(arguments[0])
        if not logs.is_dir():
            raise SystemExit(f'Log folder missing: {logs}')
        copy_matching(logs, '*.txt', 'logs')
        copy_matching(logs, '*.png', 'screens/tests')


if __name__ == '__main__':
    main(sys.argv[1:])
