#!/usr/bin/env python3
"""Build program-local C48 SSX and ZX-UX TZX files with the frozen SDK.

Usage: python build.py [--sdk PATH] [25-galaxians 58-invaders ...]
With no program arguments, build each numbered program that has C48/*.c.
Only writes under the corresponding numbered program's C48/ directory.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
COMMON = ROOT / 'c48lib'

PROGRAM_ORDER = (
    '01-minelay', '02-fall-guy', '03-tug-of-war', '04-horse-race',
    '05-championship-boxing', '06-motocross', '07-critical-path-analysis',
    '08-chomper', '09-battleships', '10-tanx', '11-defend', '12-flying-bomb',
    '13-radio-power', '14-scuba', '15-endings', '16-snap', '17-paypackets',
    '18-newmarket', '19-hobday-expenses', '20-ambush', '21-numbers',
    '22-top-trainer', '23-biorhythms', '24-aben', '25-galaxians',
    '26-sheep-dog-trials', '27-picture-pairs', '28-dam-busters', '29-oxo',
    '30-space-traffic', '31-dam-eaters', '32-buzzy-bee', '33-heli-bomber',
    '34-grand-prix', '35-giant-rats', '36-postman', '37-xmas-eve',
    '38-morse-tutor', '39-flying-geese', '40-wordsum',
    '41-asset-stripper', '42-bricklayer', '43-dogfight', '44-evolution-1',
    '45-evolution-2', '46-evolution-3', '47-exocet', '48-energy-field',
    '49-drag-racer', '50-moonlander', '51-anagrammatic', '52-stellar-run',
    '53-russian-roulette', '54-swordsman', '55-hangman', '56-roots',
    '57-bulls-and-cows', '58-invaders', '59-mushroom-invasion',
    '60-countabout',
)


def build_one(program: Path, sdk: Path) -> None:
    sources = sorted((program / 'C48').glob('*.c'))
    if len(sources) != 1:
        raise ValueError(f'{program.name}: expected exactly one C48 source')
    src = sources[0]
    stem = src.stem
    if len(stem) > 10:
        raise ValueError(f'{program.name}: cassette name {stem!r} exceeds 10 bytes')
    glyphs = src.with_name(stem + '-glyphs.asm')
    # ras does not support INCLUDE. rcc automatically links <stem>.asm.
    parts = [COMMON / 'c48lib.asm', COMMON / 'c48lib-font.asm']
    if glyphs.is_file():
        parts.append(glyphs)
    asm = src.with_suffix('.asm')
    asm.write_bytes(b'; Generated from c48lib and per-program glyphs. Do not edit.\n'
                    + b'\n'.join(p.read_bytes().rstrip(b'\r\n') for p in parts)
                    + (b'\n' if glyphs.is_file() else
                       b'\n        section data\nc48_game_glyphs:\n        ds 256\n'))
    # Import only frozen SDK modules; do not write anything to SDK checkout.
    from rcc import driver
    import rtap
    output = src.with_suffix('.ssx')
    if driver.main([str(src), '-o', str(output)]):
        raise RuntimeError(f'{src}: compilation/link failed')
    data = output.read_bytes()
    header, code = rtap.records(data, stem)
    title = ('ZX-UX C48 ' + stem).encode('ascii')
    tape = (b'ZXTape!\x1a\x01\x14' + bytes((0x30, len(title))) + title)
    rtap.write(str(src.with_suffix('.tzx')), tape, [(1000, header), (2000, code)])
    print(f'{program.name}: {stem}.ssx ({len(data)} bytes), {stem}.tzx')


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--sdk', type=Path, default=ROOT.parent.parent / 'zx-ux-sdk')
    cli.add_argument('programs', nargs='*', help='numbered folder names')
    args = cli.parse_args()
    sdk = args.sdk.resolve()
    if not (sdk / 'rcc' / 'driver.py').is_file():
        raise SystemExit('C48 SDK not found: ' + str(sdk))
    # Import frozen SDK modules without generating __pycache__ in the checkout.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(sdk))
    wanted = set(args.programs)
    unknown = wanted.difference(PROGRAM_ORDER)
    if unknown:
        raise SystemExit('Unknown numbered program: ' + ', '.join(sorted(unknown)))
    # The listing is intentionally identical to the historical BASIC directory
    # order. Do not use alphabetical glob order for the build sequence.
    for name in PROGRAM_ORDER:
        if wanted and name not in wanted:
            continue
        folder = ROOT / name
        if not folder.is_dir() or not (folder / 'C48').is_dir():
            if wanted:
                raise SystemExit('No C48 port for ' + name)
            continue
        build_one(folder, sdk)


if __name__ == '__main__':
    main()
