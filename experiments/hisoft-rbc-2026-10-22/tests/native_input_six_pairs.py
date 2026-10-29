#!/usr/bin/env python3
"""Independently build six original INPUT BAS/TZX pairs via opt-in native RBC.

The generated images and per-side diagnostics remain untracked under build/tmp.
No original BASIC, published SSX, ROM, or ZX-UX system tape is modified.
A successful link does not establish Sinclair ROM edit-control equivalence.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
SDK = ROOT / 'src/zx-ux-sdk'
sys.path[:0] = [str(STAGE), str(SDK)]
from dual_source import convert_tzx

GAMES = ('01-minelay', '07-critical-path-analysis', '23-biorhythms',
         '30-space-traffic', '39-flying-geese', '56-roots')
ORIGINALS = ROOT / 'src/bonus/60-programs'
TEMP = ROOT / 'build/tmp/rbc-input-six-pairs'
CLI = STAGE / 'native_rbc_cli.py'
CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR',
    str(ROOT / 'build/tmp/rbc-inputs/upstream-pyhsb')))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE',
    str(ROOT / 'build/tmp/rbc-inputs/hisoft48.tap')))
ROM = SDK / 'rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'


def digest(data: bytes):
    return hashlib.sha256(data).hexdigest()


def one(name: str, side: str, source: Path, deadline: int):
    folder = TEMP / name
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f'from-{side}.ssx'
    info = folder / f'{side}-report.json'
    dest.unlink(missing_ok=True)
    info.unlink(missing_ok=True)
    cmd = [sys.executable, '-B', str(CLI), str(source), '--compiler',
           str(CHECKPOINT), '--frontend', str(FRONTEND), '--tape', str(TAPE),
           '--rom', str(ROM), '--max', '14000', '--input-backend', 'zxux',
           '-o', str(dest), '--report', str(info)]
    try:
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                             text=True, timeout=deadline, check=False)
        result = {'exit': run.returncode, 'stdout': run.stdout,
                  'stderr': run.stderr}
    except subprocess.TimeoutExpired as exc:
        result = {'exit': None, 'error': 'time limit exceeded',
                  'stdout': str(exc.stdout), 'stderr': str(exc.stderr)}
    if result['exit'] == 0 and dest.is_file() and info.is_file():
        data = dest.read_bytes()
        report = json.loads(info.read_text())
        if (report.get('native_linker') != 'ras/rld' or
                not report.get('native_three_base_source_verified') or
                not report.get('input_source_bridge_three_base_verified') or
                report.get('optimizer_used') or
                report.get('file') != len(data) or
                max(report.get('file', 999999), report.get('total', 999999)) > 14000):
            result['error'] = 'invalid native link/relocation/memory report'
            result['exit'] = 1
        else:
            result['sha256'] = digest(data)
            result['size'] = len(data)
            result['memory'] = {k: report[k] for k in
                                ('file', 'image', 'bss', 'stack', 'total')}
    (folder / f'{side}-outcome.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'{name} {side}: exit={result["exit"]} '
          f'bytes={result.get("size", "n/a")} '
          f'sha256={result.get("sha256", "n/a")}', flush=True)
    return result


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('games', nargs='*', default=[])
    a.add_argument('--jobs', type=int, default=3)
    a.add_argument('--timeout', type=int, default=2400)
    args = a.parse_args(argv)
    if not 1 <= args.jobs <= 5 or not 30 <= args.timeout <= 2400:
        a.error('jobs must be 1..5, timeout 30..2400 seconds')
    if len(args.games) != len(set(args.games)) or set(args.games) - set(GAMES):
        a.error('unknown or duplicate game')
    selected = sorted(args.games or GAMES)
    required = (CHECKPOINT/'rbc.py', CHECKPOINT/'font32.bin',
                FRONTEND/'compiler.py', TAPE, ROM, SYSTEM, FROZEN)
    if not all(p.is_file() for p in required):
        raise ValueError('original checked native compiler, ROM and ZX-UX required')
    if SYSTEM.read_bytes() != FROZEN.read_bytes():
        raise ValueError('rebuilt ZX-UX differs from frozen release')
    originals = [ORIGINALS/n/'BASIC'/(n+ext)
                 for n in selected for ext in ('.bas', '.tzx')]
    if not all(p.is_file() for p in originals):
        raise ValueError('missing original BAS/TZX')
    before = {str(p): digest(p.read_bytes()) for p in originals}
    sys.path[:0] = [str(FRONTEND), str(CHECKPOINT)]
    import rbc
    import source
    import compiler
    import hbcimage
    rom = ROM.read_bytes()
    kws = source.Keywords(rom)
    fp = compiler.Compiler(hbcimage.Image.from_tape(TAPE), rom, ramtop=65367).fp
    prepared = []
    failed = []
    for name in selected:
        basic = ORIGINALS/name/'BASIC'
        bas = basic/(name+'.bas')
        tzx = basic/(name+'.tzx')
        converted = TEMP/name/'from-tape'/(name+'.bas')
        prepared.append((name, 'bas', bas))
        try:
            conv = convert_tzx(tzx, bas, converted, rbc, source, kws, fp)
            print(f'{name}: independent TZX conversion PASS, '
                  f'{conv["source_lines"]} BASIC lines', flush=True)
            prepared.append((name, 'tzx', converted))
        except Exception as exc:
            failed.append(name + ': TZX ' + type(exc).__name__ + ': ' + str(exc))
            print(f'{name}: TZX CONVERSION FAILED: {exc}', flush=True)
    outcomes = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {pool.submit(one, name, side, path, args.timeout): (name, side)
                for name, side, path in prepared}
        for future in as_completed(jobs):
            name, side = jobs[future]
            try:
                outcomes[(name, side)] = future.result()
            except Exception as exc:
                failed.append(name + '/' + side + ': ' + str(exc))
    verified = []
    for name in selected:
        a, b = outcomes.get((name, 'bas')), outcomes.get((name, 'tzx'))
        if a is None or b is None or a['exit'] != 0 or b['exit'] != 0:
            failed.append(name + ': BAS/TZX independent compilation unavailable')
            continue
        lhs = (TEMP/name/'from-bas.ssx').read_bytes()
        rhs = (TEMP/name/'from-tzx.ssx').read_bytes()
        if lhs != rhs:
            first = next((p for p in range(min(len(lhs), len(rhs)))
                          if lhs[p] != rhs[p]), min(len(lhs), len(rhs)))
            failed.append(f'{name}: BAS/TZX SSX mismatch, first offset {first}')
        else:
            verified.append(name)
            print(f'{name}: BAS/TZX byte-identical native SSX', flush=True)
    if {str(p): digest(p.read_bytes()) for p in originals} != before:
        failed.append('original BAS/TZX hashes changed')
    print(f'SIX PAIRS: {len(verified)}/{len(selected)} passed; '
          f'{len(failed)} failure messages', flush=True)
    for entry in failed:
        print('BLOCKED: ' + entry, flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
