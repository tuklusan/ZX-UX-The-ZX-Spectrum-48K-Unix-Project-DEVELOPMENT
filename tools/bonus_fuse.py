#!/usr/bin/env python3
"""Replay and capture the bonus C48 pilot programs on native ZX-UX/FUSE.

The boot tape comes from release/dist/zx-ux/ZX-UX.tzx. Each SSX is
appended as its own cassette program and loaded using /dev/cassette.
Run: python3 -B tools/bonus_fuse.py --help
"""
import argparse
from pathlib import Path

import fuse_portfolio

ROOT = Path(__file__).resolve().parents[1]
BONUS = ROOT / 'release/dist/bonus/60-programs'
SCENES = {
    'anagram:intro': ('51-anagrammatic', 'anagram', '01-intro.png', []),
    'anagram:main': ('51-anagrammatic', 'anagram', '02-main.png',
                     [(0.7, ' '), (1.2, 'AE\n'), (1.2, 'n')]),
    'anagram:result': ('51-anagrammatic', 'anagram', '03-after-input.png',
                       [(0.7, ' '), (1.2, 'AE\n'), (1.2, 'n'), (1.2, '2\n')]),
    'roulette:intro': ('53-russian-roulette', 'roulette', '01-intro.png', []),
    'roulette:result': ('53-russian-roulette', 'roulette', '02-result.png',
                        [(0.7, 'aaab')]),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=SCENES, required=True)
    parser.add_argument('--fuse', required=True, type=Path)
    parser.add_argument('--assets', required=True, type=Path)
    parser.add_argument('--libdir', default=None, type=Path)
    parser.add_argument('--rom', default=ROOT/'release/src/zx-ux/rom/48.rom', type=Path)
    parser.add_argument('--display', type=int, default=98)
    parser.add_argument('--boot-wait', type=int, default=90)
    parser.add_argument('--speed', type=int, default=300)
    args = parser.parse_args()
    folder, name, image, steps = SCENES[args.case]
    args.fuse = args.fuse.resolve()
    args.assets = args.assets.resolve()
    args.rom = args.rom.resolve()
    if args.libdir is not None:
        args.libdir = args.libdir.resolve()
    args.wait = 3
    args.multitask_wait = 3
    args.libdir = args.libdir
    fuse_portfolio.BIN = BONUS / folder / 'C48/bin/ssx'
    target = BONUS / folder / 'C48/screenshots/fuse' / image
    fuse_portfolio.run_case((name,), target, args,
                            {'fuse_speed': args.speed, 'fuse_wait': 2,
                             'input_steps': steps})


if __name__ == '__main__':
    main()
