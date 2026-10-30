#!/usr/bin/env python3
"""Capture accepted BASIC games through genuine Fuse/ZX-UX cassette loading."""
from __future__ import annotations

import argparse
import concurrent.futures
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from basic_portfolio import cases, write_gallery
from fuse_portfolio import run_case

OUT = ROOT / 'dist/screenshots/fuse/basic'


def capture(i, collection, ssx, label, opts):
    local = argparse.Namespace(**vars(opts))
    local.display = opts.display + i + 1
    out = OUT / collection / (ssx.stem + '.png')
    run_case((label,), out, local,
             {'programs': {label: ssx}, 'capture_delay': 1.0,
              'fuse_wait': opts.wait, 'sample_step': .2})


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fuse', type=Path, required=True)
    p.add_argument('--rom', type=Path, default=ROOT / 'src/zx-ux/rom/48.rom')
    p.add_argument('--assets', type=Path, required=True)
    p.add_argument('--libdir', type=Path)
    p.add_argument('--only', default='')
    p.add_argument('--display', type=int, default=400)
    p.add_argument('--jobs', type=int, default=6)
    p.add_argument('--boot-wait', type=int, default=90)
    p.add_argument('--wait', type=int, default=8)
    p.add_argument('--speed', type=int, default=100)
    p.add_argument('--multitask-wait', type=int, default=60)
    a = p.parse_args(argv)
    for attr in ('fuse', 'rom', 'assets', 'libdir'):
        value = getattr(a, attr)
        if value is not None:
            setattr(a, attr, value.resolve())
    if not 1 <= a.jobs <= 16:
        p.error('--jobs must be 1..16')
    wanted = set(a.only.split(',')) if a.only else None
    runs = [(collection, ssx, label) for collection, ssx, label in cases()
            if wanted is None or ssx.stem in wanted]
    problems = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.jobs) as workers:
        pending = {workers.submit(capture, i, *entry, a): entry[1].stem
                   for i, entry in enumerate(runs)}
        for task in concurrent.futures.as_completed(pending):
            try:
                task.result()
            except Exception as exc:
                print('BASIC Fuse FAIL', pending[task], exc, file=sys.stderr, flush=True)
                problems.append(pending[task])
    if wanted is not None:
        problems.extend(sorted(wanted - {e[1].stem for e in runs}))
    count = write_gallery(OUT, 'Fuse')
    if wanted is None and count != len(runs):
        problems.append('incomplete BASIC Fuse gallery')
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
