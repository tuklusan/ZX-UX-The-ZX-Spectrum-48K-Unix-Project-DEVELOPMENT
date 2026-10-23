#!/usr/bin/env python3
"""Check upstream HiSoft PAUSE 0 through native ZX-UX game controls.

RBC must compile the unchanged original PAUSE statement. This check uses
its ordinary compiler output, with no source rewrite or port override.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def check_finite_pause(root: Path, trial: Path):
    listing = trial / 'finite-pause.bas'
    listing.write_text('10 BORDER 0:PAPER 0:INK 7:CLS\n'
                       '20 PRINT AT 5,2;"BEFORE"\n'
                       '30 PAUSE 12\n'
                       '40 PRINT AT 6,2;"AFTER"\n'
                       '50 GO TO 50\n')
    binary = trial / 'finite-pause.ssx'
    command = [sys.executable, str(trial / 'rbc/rbc.py'), str(listing),
               '--frontend', str(root / 'upstream-pyhsb'),
               '--sdk', str(root / 'src/zx-ux-sdk'),
               '--rom', str(root / 'src/zx-ux-sdk/rom/48.rom'),
               '--tape', str(trial / 'hisoft48.tap'),
               '-o', str(binary)]
    subprocess.run(command, cwd=root, check=True, timeout=110)
    sys.path.insert(0, str(root / 'dist/sdk/bin/py'))
    import rvm
    options = rvm.Options()
    options.prog = str(binary)
    options.system = str(root / 'dist/zx-ux/tzx/ZX-UX.tzx')
    options.headless = True
    runner = rvm.Runner(options)
    runner.start()
    for _ in range(9000):
        runner.frame()
        if runner.fg and runner.fg.started is not None:
            break
    else:
        raise AssertionError('finite PAUSE fixture never started')
    before = after = None
    for frame in range(60):
        runner.frame()
        bitmap, _ = runner.picture()
        pixels = sum(int(byte).bit_count() for byte in bitmap[:6144])
        if before is None and 150 <= pixels <= 220:
            before = frame
        elif before is not None and after is None and pixels >= 250:
            after = frame
            break
    if before is None or after is None or not 9 <= after - before <= 19:
        raise AssertionError(f'finite PAUSE timing invalid: before={before}, after={after}')
    return after - before


def probe(root: Path, trial: Path):
    listing = root / 'src/bonus/60-programs/25-galaxians/BASIC/25-galaxians.bas'
    source = listing.read_bytes()
    if b'8050 PAUSE 0:CLS :RETURN' not in source:
        raise AssertionError('expected unchanged PAUSE 0 in original Galaxians')
    binary = trial / '25-galaxians-text.ssx'
    if not binary.is_file():
        raise AssertionError('original text build missing')
    from gameplay_ports import play
    result = play(root, binary, trial / 'rbc-native-pause-controls')
    summary = {'original_listing_sha256': hashlib.sha256(source).hexdigest(),
               'native_pause_compiled': True,
               'finite_pause_frames': check_finite_pause(root, trial),
               'left_moved': result['left_moved'],
               'right_moved': result['right_moved'],
               'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
    (trial / 'native-pause-result.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('NATIVE PAUSE', json.dumps(summary), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--trial', type=Path, default=Path('trial-result'))
    args = parser.parse_args()
    probe(args.root.resolve(), args.trial.resolve())


if __name__ == '__main__':
    main()
