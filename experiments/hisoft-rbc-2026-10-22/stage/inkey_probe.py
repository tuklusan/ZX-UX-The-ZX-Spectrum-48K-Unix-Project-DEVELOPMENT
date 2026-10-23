#!/usr/bin/env python3
"""Exercise immediate INKEY$ through the real ZX-UX keyboard and CPU model.

The checked sample shows READY with no key, HIT and HELD during a held key,
and RELEASED after the physical key is released. The source ZIP is read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from frame_probe import screen_letters


def run(root: Path, output: Path) -> dict:
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
    import rvm
    import zxux

    archive = root / 'experiments/hisoft-rbc-2026-10-22/rbc-fresh-chat-2026-10-22.zip'
    with zipfile.ZipFile(archive) as zf:
        binary = zf.read('scratch/out/inkey-regenerated.ssx')
        font = zf.read('scratch/rbc/font32.bin')
    output.mkdir(parents=True, exist_ok=True)
    ssx = output / 'inkey-example.ssx'
    ssx.write_bytes(binary)
    options = rvm.Options()
    options.prog = str(ssx)
    options.system = str(root / 'dist/zx-ux/tzx/ZX-UX.tzx')
    options.headless = True
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    for _ in range(9000):
        runner.frame()
        if runner.fg is not None and runner.fg.started is not None:
            break
    else:
        raise RuntimeError('INKEY$ program failed to start on ZX-UX')

    def sample(name: str, frames: int, words: tuple[str, ...]) -> dict:
        for _ in range(frames):
            runner.frame()
        bitmap, border = runner.picture()
        png = output / f'inkey-{name}.png'
        rvm.write_png(bitmap, str(png), border)
        lines = screen_letters(bitmap, font)
        found = {word: any(word in line for line in lines) for word in words}
        return {'stage': name, 'frames': runner.session.m.frame - runner.fg.started,
                'keyboard_state': runner.session.kb.state,
                'physical_key_scans': runner.session.m.ints,
                'foreground_exit': runner.fg.status,
                'found_words': found,
                'screen_sha256': hashlib.sha256(bitmap).hexdigest(),
                'screenshot': png.name}

    rows = [sample('idle', 30, ('READY',))]
    runner.session.kb.add([('press', zxux.char_keys('z'), 24)])
    rows.append(sample('held', 24, ('READY', 'HIT', 'HELD')))
    rows.append(sample('released', 40, ('RELEASED',)))
    good = all(all(row['found_words'].values()) for row in rows)
    good &= rows[0]['keyboard_state'] == 'idle'
    good &= rows[1]['keyboard_state'] == 'held'
    good &= rows[2]['keyboard_state'] == 'idle'
    good &= runner.fg.status == 0
    result = {'sample_sha256': hashlib.sha256(binary).hexdigest(),
              'real_zxux': True, 'passed': bool(good), 'phases': rows}
    (output / 'inkey-result.json').write_text(json.dumps(result, indent=2) + '\n')
    if not good:
        raise AssertionError('INKEY$ did not pass its no-key, press, hold, release sequence')
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--out', type=Path, default=Path('trial-result/rbc-game-probe'))
    args = parser.parse_args()
    result = run(args.root.resolve(), args.out.resolve())
    print(f"INKEY$ real ZX-UX keyboard: {'PASS' if result['passed'] else 'FAIL'}", flush=True)


if __name__ == '__main__':
    main()
