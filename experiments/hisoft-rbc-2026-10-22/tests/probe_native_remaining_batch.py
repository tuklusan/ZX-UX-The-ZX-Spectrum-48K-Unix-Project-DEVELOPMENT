#!/usr/bin/env python3
"""Bounded, isolated real-ZX-UX probes for unfinished published games.

Collects bounded emulator observations from the original published programs.
A successful command records observations but does not establish a complete
gameplay round. Game binaries and source files are read without modification.

Usage from repository root:
    python3 -B experiments/hisoft-rbc-2026-10-22/tests/probe_native_remaining_batch.py \
        --output build/tmp/remaining-probes.json --jobs 10
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
GAMES = ROOT / 'src/bonus/60-programs'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
FONT = ROOT / 'build/tmp/rbc-recovered/rbc/font32.bin'
# Exactly ten independent first-batch trials, followed by the two other
# unfinished published games; no off-list game binaries are generated.
CASES = (
    ('07-critical-path-analysis', '{WAIT 200}{ENTER}{WAIT 150}{ENTER}{WAIT 150}{ENTER}{WAIT 150}1{ENTER}{WAIT 100}12{ENTER}', 2400),
    ('09-battleships', '{WAIT 300}a{WAIT 250}1{ENTER}{WAIT 120}D4{ENTER}', 2400),
    ('10-tanx', '{WAIT 220}a{WAIT 150}45{ENTER}{WAIT 120}5{ENTER}{WAIT 120}45{ENTER}{WAIT 120}5{ENTER}', 2600),
    ('17-paypackets', '{WAIT 650}{ENTER}{WAIT 100}12.34{ENTER}{WAIT 120}2{ENTER}', 2100),
    ('18-newmarket', '{WAIT 500}a{WAIT 300}a{WAIT 300}1{ENTER}', 2400),
    ('28-dam-busters', '{WAIT 250}a{WAIT 250}a{WAIT 150}9', 2900),
    ('43-dogfight', '{WAIT 100}a{WAIT 800}x{WAIT 100}x', 3500),
    ('47-exocet', '{WAIT 100}a{WAIT 200}' + '0{WAIT 120}' * 20, 3700),
    ('56-roots', '{WAIT 350}{ENTER}{WAIT 200}{ENTER}{WAIT 200}{ENTER}', 2700),
    ('57-bulls-and-cows', '{WAIT 280}a{WAIT 450}2{ENTER}{WAIT 200}1234{ENTER}', 2200),
    ('03-tug-of-war', '{WAIT 200}a{WAIT 200}a', 1500),
    ('59-mushroom-invasion', '{WAIT 1400}a{WAIT 100}1', 3500),
)


def worker(name: str, keys: str, frames: int) -> dict:
    sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'), str(Path(__file__).parent)]
    import rld
    import rvm
    from test_native_oxo_complete_round import text_row

    game = GAMES / name
    bas, tzx, ssx = (game / 'BASIC' / (name + '.bas'),
                     game / 'BASIC' / (name + '.tzx'),
                     game / 'bin' / (name + '.ssx'))
    sources = [bas, tzx, ssx, ROM]
    originals = [p.read_bytes() for p in sources]
    sha = [sha256(x).hexdigest() for x in originals]
    binary = originals[2]
    parsed = rld.parse_ssx(binary)
    file_bytes = len(binary)
    image = len(parsed['image'])
    bss = parsed['bss']
    stack = parsed['stack']
    assert parsed['entry'] == 0
    assert max(file_bytes, image + bss + stack) <= 14000
    assert SYSTEM.read_bytes() == FROZEN.read_bytes()
    font = FONT.read_bytes()
    romfont = originals[3][0x3d00:0x4000]
    assert len(font) == len(romfont) == 768

    o = rvm.Options()
    o.prog, o.keys, o.frames, o.system = str(ssx), keys, frames, str(SYSTEM)
    o.cache, o.headless = True, True
    run = rvm.Runner(o)
    run.start()
    observed = {}
    start = time.monotonic()
    frames_done = 0
    captures = {400, frames // 2, frames - 1}
    for _ in range(frames + 3000):
        run.frame()
        if run.fg.started is None:
            continue
        relative = run.session.m.frame - run.fg.started
        if relative in captures or run.fg.ended is not None:
            picture, border = run.picture()
            assert len(picture) == 6912
            rows = [text_row(picture, line, font).strip() for line in range(24)]
            romrows = [text_row(picture, line, romfont).strip() for line in range(24)]
            observed[str(relative)] = {
                'framebuffer_sha256': sha256(picture).hexdigest(),
                'rows': {str(i): val for i, val in enumerate(rows) if val and
                         any(ch.isalnum() for ch in val)},
                'rom_rows': {str(i): val for i, val in enumerate(romrows) if val and
                             any(ch.isalnum() for ch in val)},
            }
            if os.environ.get('RBC_PROBE_CAPTURE_DIR') and relative >= frames - 1:
                d = Path(os.environ['RBC_PROBE_CAPTURE_DIR'])
                d.mkdir(parents=True, exist_ok=True)
                rvm.write_png(picture, str(d / (name + '-bounded.png')), border)
        frames_done = relative
        if run.fg.ended is not None or relative >= frames:
            break
    else:
        raise AssertionError('native program never started within bounded boot')
    assert run.fg.started is not None
    assert [p.read_bytes() for p in sources] == originals
    return {
        'game': name, 'keys': keys, 'frame_limit': frames,
        'observed_frames': frames_done, 'runtime_seconds': round(time.monotonic()-start, 3),
        'process_ended': run.fg.ended is not None,
        'exit_status': run.fg.status if run.fg.ended is not None else None,
        'screen_owned_when_live': run.fg.ended is None and run.session.owns_screen(run.fg.pid),
        'input_busy': run.session.kb.busy(),
        'sha256': dict(zip(('bas','tzx','ssx','rom'), sha)),
        'file_bytes': file_bytes, 'image_bytes': image,
        'bss_bytes': bss, 'stack_bytes': stack,
        'total_bytes': image + bss + stack,
        'samples': observed,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    p.add_argument('--jobs', type=int, default=10)
    p.add_argument('--batch', choices=['ten', 'two', 'all'], default='ten')
    p.add_argument('--frame-cap', type=int, default=0)
    p.add_argument('--child-timeout', type=int, default=110)
    p.add_argument('--worker', action='store_true')
    p.add_argument('--name')
    p.add_argument('--keys')
    p.add_argument('--frames', type=int)
    args = p.parse_args()
    if args.worker:
        print(json.dumps(worker(args.name, args.keys, args.frames), sort_keys=True))
        return 0
    chosen = CASES[:10] if args.batch == 'ten' else CASES[10:] if args.batch == 'two' else CASES
    if args.frame_cap:
        assert args.frame_cap >= 400
        chosen = tuple((name, keys, min(frames,args.frame_cap))
                       for name,keys,frames in chosen)
    assert 1 <= args.jobs <= 10
    assert SYSTEM.read_bytes() == FROZEN.read_bytes()
    start = time.monotonic()
    results = {}
    def run_child(case):
        name, keys, frames = case
        cmd = [sys.executable, '-B', str(Path(__file__).resolve()), '--output', args.output,
               '--worker', '--name', name, '--keys', keys, '--frames', str(frames)]
        try:
            r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=args.child_timeout,
                               env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        except subprocess.TimeoutExpired:
            return name, {'game': name, 'error': f'{args.child_timeout}-second isolated probe timeout',
                          'frames_requested': frames}
        if r.returncode != 0:
            return name, {'game': name, 'error': 'isolated probe failed',
                          'exit_code': r.returncode,
                          'stderr_tail': r.stderr[-500:]}
        try:
            return name, json.loads(r.stdout)
        except json.JSONDecodeError:
            return name, {'game': name, 'error': 'non-JSON worker output',
                          'stdout_tail': r.stdout[-300:]}
    def write_results(complete: bool):
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps({
            'description': 'Original ZX-UX emulator framebuffer observations and process metadata',
            'batch': args.batch, 'processes': len(chosen),
            'max_parallel_jobs': args.jobs, 'complete': complete,
            'elapsed_wall_seconds': round(time.monotonic()-start,3),
            'results': {name: results.get(name, {'pending':True}) for name,_,_ in chosen},
        }, indent=2, sort_keys=True) + '\n')
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_child, case) for case in chosen]
        for f in as_completed(futures):
            name, result = f.result()
            results[name] = result
            write_results(False)
            print(name, 'ERROR' if 'error' in result else 'OBSERVED', flush=True)
    write_results(True)
    return 0 if all('error' not in x for x in results.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
