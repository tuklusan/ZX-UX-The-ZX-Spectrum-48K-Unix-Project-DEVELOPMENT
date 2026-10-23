#!/usr/bin/env python3
"""Capture real game frames with RBC's default 48K ROM font.

The established native game-frame and sprite checks run unchanged. This
runner supplies the actual 48K ROM printable glyphs and separately confirms
that the live process points CHARS at the original ROM font throughout.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def printable_rom_font(raw: bytes) -> bytes:
    if len(raw) != 16384:
        raise ValueError('expected the original 16 KB Spectrum ROM')
    return raw[0x3D00:0x4000]


def verify_rom_pointer(captures: list[dict]) -> None:
    if not captures:
        raise AssertionError('native captures are missing')
    bad = [(row.get('label'), row.get('chars_pointer')) for row in captures
           if row.get('chars_pointer') != 0x3C00]
    if bad:
        raise AssertionError('native CHARS pointer differs from the 48K ROM: '+repr(bad))
    if any(not row.get('font_state', {}).get('font_intact') for row in captures):
        raise AssertionError('48K ROM character bytes do not match')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--trial', type=Path, default=Path('trial-result'))
    args = parser.parse_args()
    root, trial = args.root.resolve(), args.trial.resolve()
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
    import rvm  # noqa: F401
    from frame_probe import GAMES, run_game
    font = printable_rom_font((root / 'src/zx-ux-sdk/rom/48.rom').read_bytes())
    directory = trial / 'rbc-game-probe'
    directory.mkdir(parents=True, exist_ok=True)
    system = root / 'dist/zx-ux/tzx/ZX-UX.tzx'
    results = []
    for number, short_name in GAMES:
        name = f'{number:02d}-{short_name}'
        binary = trial / (name + '-tape.ssx')
        if not binary.is_file():
            continue
        original = root / f'src/bonus/60-programs/{name}/BASIC/SCREENSHOTS/02-MAIN.png'
        report = run_game(binary, system, font, original, directory)
        verify_rom_pointer(report['captures'])
        report['font_source'] = '48K ROM'
        results.append(report)
    path = directory / 'report.json'
    path.write_text(json.dumps(results, indent=2) + '\n')
    for row in results:
        print(f"PROBE {row['program']}: {row['capture_count']} actual native frames, "
              f"screen_changed={row['screen_changed_after_input']}, "
              f"nonblank={row['all_frames_nonblank']}", flush=True)
    print(f'Native game probe results: {path}', flush=True)


if __name__ == '__main__':
    main()
