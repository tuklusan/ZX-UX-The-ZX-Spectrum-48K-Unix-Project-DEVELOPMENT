#!/usr/bin/env python3
"""Check genuine ZX-UX Galaxians left/right movement after SPACE starts play.

The ZX-UX emulator reads ULA keyboard ports without input overrides.
The ZX-UX system, ROM, SSX1 program and BASIC sources remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def player_columns(bitmap: bytes):
    """Nonblank cells in the original ship's bottom display row (row 21)."""
    if len(bitmap) != 6912:
        raise ValueError('expected complete Spectrum screen')
    result = []
    for column in range(32):
        for line in range(21 * 8, 22 * 8):
            offset = ((line & 0xC0) << 5) | ((line & 7) << 8) | ((line & 0x38) << 2) | column
            if bitmap[offset]:
                result.append(column)
                break
    return result


def play(root: Path, binary: Path, output: Path) -> dict:
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
    import rvm
    import zxux

    opts = rvm.Options()
    opts.prog = str(binary)
    opts.system = str(root / 'dist/zx-ux/tzx/ZX-UX.tzx')
    opts.headless = True
    runner = rvm.Runner(opts)
    runner.start()
    # Select the supported Issue 2 hardware model; no port read is overridden.
    runner.session.m.ula_issue = 2
    for _ in range(9000):
        runner.frame()
        if runner.fg and runner.fg.started is not None:
            break
    else:
        raise RuntimeError('Galaxians did not start in native ZX-UX')

    def advance(frames):
        for _ in range(frames):
            runner.frame()

    output.mkdir(parents=True, exist_ok=True)
    images = []

    def sample(label):
        bitmap, border = runner.picture()
        path = output / (label + '.png')
        rvm.write_png(bitmap, str(path), border)
        cols = player_columns(bitmap)
        images.append({'phase': label, 'png': path.name, 'player_columns': cols,
                       'screen_sha256': hashlib.sha256(bitmap).hexdigest(),
                       'keyboard_interrupt_scans': runner.session.m.ints})
        return cols

    advance(70)
    runner.session.kb.add([('press', zxux.char_keys(' '), 30)])
    advance(100)
    start = sample('galaxians-start')
    runner.session.kb.add([('press', zxux.char_keys('z'), 110)])
    advance(145)
    left = sample('galaxians-left')
    runner.session.kb.add([('press', zxux.char_keys('x'), 110)])
    advance(145)
    right = sample('galaxians-right')
    runner.session.kb.add([('press', zxux.char_keys('m'), 110)])
    advance(145)
    sample('galaxians-fire')
    moved_left = bool(start and left and min(left) < min(start))
    moved_right = bool(left and right and min(right) > min(left))
    result = {'game': '25-galaxians', 'source': str(binary),
              'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'ula_input': 'native emulator', 'ula_issue': 2, 'screen_rows': images,
              'left_moved': moved_left, 'right_moved': moved_right,
              'fire_pressed': True, 'fire_hit_or_score': 'not established',
              'gameplay_verified': False}
    (output / 'movement-report.json').write_text(json.dumps(result, indent=2) + '\n')
    if not moved_left or not moved_right:
        raise AssertionError('Native ship failed left or right key movement')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = play(args.root.resolve(), args.binary.resolve(), args.output.resolve())
    print('GALAXIANS native left/right:', result['left_moved'], result['right_moved'])


if __name__ == '__main__':
    main()
