"""Check original Evolution tape operations using the RBC input path."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from dual_source import convert_tzx

CASES = {'44-evolution-1': 8060, '45-evolution-2': 1860}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate5')
    ap.add_argument('--frontend', type=Path, default=ROOT / 'upstream-pyhsb')
    ap.add_argument('--tape', type=Path, default=ROOT / 'trial-result/hisoft48.tap')
    args = ap.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)

    import compiler
    import hbcimage
    import rbc
    import source
    from basic_listing import encode_strict_listing
    from dual_source import validated_lines
    from tape_policy import reject_tape_operations, UnsupportedTapeOperation

    rom = (ROOT / 'src/zx-ux-sdk/rom/48.rom').read_bytes()
    kw = source.Keywords(rom)
    fp = compiler.Compiler(hbcimage.Image.from_tape(args.tape), rom, ramtop=65367).fp
    report = {}
    for game, expected_line in CASES.items():
        original = ROOT / 'src/bonus/60-programs' / game / 'BASIC'
        bas = original / (game + '.bas')
        tzx = original / (game + '.tzx')
        case = work / game
        case.mkdir(parents=True, exist_ok=True)
        converted_bas = case / 'from-tzx.bas'
        conversion = convert_tzx(tzx, bas, converted_bas, rbc, source, kw, fp)
        paths = {'bas': bas, 'tzx': converted_bas}
        item = {'original_bas_sha256': sha(bas),
                'original_tzx_sha256': sha(tzx), 'conversion': conversion}
        for mode, input_path in paths.items():
            encoded = encode_strict_listing(input_path.read_text(encoding='ascii'))
            try:
                reject_tape_operations(validated_lines(encoded), kw.TOKEN)
            except UnsupportedTapeOperation as exc:
                scanned = str(exc)
                if f'Line {expected_line}' not in scanned or 'LOAD' not in scanned:
                    raise AssertionError(game + ': unexpected tape rejection: ' + scanned)
            else:
                raise AssertionError(game + ': unsafe tape operation admitted')
            target = case / ('from-' + mode + '.ssx')
            command = [sys.executable, str(ROOT / 'trial-result/rbc/rbc.py'),
                       str(input_path), '--frontend', str(args.frontend),
                       '--sdk', str(ROOT / 'src/zx-ux-sdk'),
                       '--rom', str(ROOT / 'src/zx-ux-sdk/rom/48.rom'),
                       '--tape', str(args.tape), '--max', '12000', '-o', str(target)]
            p = subprocess.run(command, cwd=ROOT, capture_output=True,
                               text=True, timeout=100)
            combined = p.stdout + '\n' + p.stderr
            row = {'input_sha256': sha(input_path), 'exit': p.returncode,
                   'stdout': p.stdout, 'stderr': p.stderr,
                   'binary_created': target.exists(), 'token_rejection': scanned}
            item[mode] = row
            print('GATE5', game, mode, json.dumps(row), flush=True)
            if p.returncode == 0 or target.exists():
                raise AssertionError(game + ': unsupported tape input linked')
            if 'RBC_TAPE_LOAD' not in combined or f'Line: {expected_line}' not in combined:
                raise AssertionError(game + ': incomplete tape diagnostic')
        report[game] = item
        (case / 'outcome.json').write_text(json.dumps(item, indent=2) + '\n')
    (work / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    if len(report) != len(CASES):
        raise AssertionError('Not every original Evolution pair was attempted')


if __name__ == '__main__':
    check()
