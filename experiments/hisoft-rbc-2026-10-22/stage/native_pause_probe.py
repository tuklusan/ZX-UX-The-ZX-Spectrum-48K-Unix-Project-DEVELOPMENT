#!/usr/bin/env python3
"""Test HiSoft's own PAUSE 0 runtime against native ZX-UX without rewriting BASIC.

This experiment copies the prepared RBC compiler and disables only the
source-level PAUSE translation in that copy. It does not change the original
BASIC, the SDK, or the production compiler used by the main test matrix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def probe(root: Path, trial: Path):
    prepared = trial / 'rbc'
    isolated = trial / 'rbc-native-pause'
    if isolated.exists():
        raise ValueError('native PAUSE test output already exists')
    shutil.copytree(prepared, isolated)
    source = isolated / 'rbc.py'
    code = source.read_text()
    prior = 'program, pause_lines = rewrite_pause_zero(program, kw, initial.fp)'
    if code.count(prior) != 1:
        raise ValueError('expected exactly one experimental PAUSE rewrite call')
    source.write_text(code.replace(prior, 'pause_lines = []', 1))

    listing = root / 'src/bonus/60-programs/25-galaxians/BASIC/25-galaxians.bas'
    before = hashlib.sha256(listing.read_bytes()).hexdigest()
    binary = trial / '25-galaxians-native-pause.ssx'
    command = [sys.executable, str(source), str(listing),
               '--frontend', str(root / 'upstream-pyhsb'),
               '--sdk', str(root / 'src/zx-ux-sdk'),
               '--rom', str(root / 'src/zx-ux-sdk/rom/48.rom'),
               '--tape', str(trial / 'hisoft48.tap'),
               '-o', str(binary),
               '--report', str(trial / '25-galaxians-native-pause.json')]
    subprocess.run(command, check=True, cwd=root, timeout=110)
    if hashlib.sha256(listing.read_bytes()).hexdigest() != before:
        raise RuntimeError('original Galaxians listing changed')
    from gameplay_ports import play
    result = play(root, binary, trial / 'rbc-native-pause-controls')
    summary = {'original_listing_sha256': before,
               'native_pause_compiled': binary.is_file(),
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
