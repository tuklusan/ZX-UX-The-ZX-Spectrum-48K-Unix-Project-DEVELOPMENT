#!/usr/bin/env python3
"""Capture the built C48 portfolio from the real ZX-UX kernel in RVM.

Usage: python3 tools/portfolio.py [--only NAME[,NAME]] [--frames N]
No C48 programs are recompiled. The two multitasking scenes are included.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'release/dist'
sys.path[:0] = [str(DIST / 'sdk/bin/py'), str(ROOT / 'tools')]
import rvm
import zxscreen
from gallery import write_gallery

SOURCES = DIST / 'assets/c48-src'
BIN = DIST / 'assets/c48-bin/ssx'
OUT = DIST / 'screenshots/rvm'
PAIRS = (('hanoi', 'queens8'), ('mobius', 'torus'))
# Captures run graphics to completion rather than using the test suite's
# short two-frame animation argument. Other programs retain test inputs.
CAPTURE = {
    'galaxy': {'args': [], 'frames': 3200, 'fuse_wait': 45, 'fuse_speed': 300},
    'goblet': {'args': [], 'frames': 3200, 'fuse_wait': 45, 'fuse_speed': 300},
    'julia': {'args': [], 'frames': 30000, 'fuse_wait': 270, 'fuse_speed': 300, 'first_fractal': True},
    'mandel': {'args': [], 'frames': 30000, 'fuse_wait': 270, 'fuse_speed': 300, 'first_fractal': True},
    'mobius': {'args': [], 'frames': 4200, 'fuse_wait': 55, 'fuse_speed': 300},
    'torus': {'args': [], 'frames': 5500, 'fuse_wait': 55, 'fuse_speed': 300},
    'kaleido': {'args': [], 'frames': 3600, 'fuse_wait': 20},
    'ball': {'args': [], 'frames': 1100, 'fuse_wait': 12},
    'invaders': {'args': [], 'keys': 'm', 'keygap': 160,
                 'frames': 2200, 'fuse_wait': 15},
}


def captures():
    configured = json.loads((ROOT / 'tests/sdk/runs.json').read_text())
    scenarios = {}
    for name, run in configured.items():
        base = name.split(':', 1)[0]
        if base not in scenarios or ':' in name and 'keys' in run and 'keys' not in scenarios[base]:
            scenarios[base] = run
    for source in sorted(SOURCES.glob('*/*.c')):
        if source.stem == 'seckern':  # deliberately un-compilable security fixture
            continue
        name = ('maze1982' if source.parent.name == 'examples' and source.stem == 'maze'
                else 'maze1996' if source.parent.name == 'games' and source.stem == 'maze1982'
                else source.stem)
        if name not in scenarios:
            scenarios[name] = {'dir': source.parent.name}
        yield name, source.parent.name, {**scenarios[name], **CAPTURE.get(name, {})}


def run_one(name, category, config, max_frames):
    executable = BIN / (name + '.ssx')
    if not executable.is_file():
        raise RuntimeError(f'missing compiled program: {executable}')
    opt = rvm.Options()
    opt.prog = str(executable)
    opt.args = [] if name == 'hanoi' else list(config.get('args', []))
    opt.keys = config.get('keys', '')
    opt.keygap = config.get('keygap', 100)
    opt.headless = True
    # Long-running games are sampled, not run to their final event.
    budget = int(config.get('frames', min(max_frames, int(config.get('zxux_frames', max_frames)))))
    runner = rvm.Runner(opt)
    runner.start()
    first_fractal = bool(config.get('first_fractal', False))
    completed = False
    for frame_index in range(budget + 3000):
        runner.frame()
        if first_fractal and runner.fg.started is not None and frame_index % 25 == 0:
            # The 48th scanline of the first fractal plots at screen y=8.
            # Test the *raw Spectrum bitmap*, including ink-black pixels.
            image = runner.session.m.screen()
            if sum(bool(v) for v in image[32:64]) >= 10:
                runner.why = 'first fractal completed'
                completed = True
                break
        reason = runner.check(limit=budget)
        if reason:
            runner.why = reason
            break
        if runner.fg.started is None and runner.session.m.frame - runner.start_frame > budget + 2500:
            raise RuntimeError(name + ': ZX-UX did not start application')
    if runner.fg.started is None:
        raise RuntimeError(name + ': loader never started application')
    if first_fractal and not completed:
        raise RuntimeError(name + ': first fractal was not completed')
    img, border = runner.picture()
    if len(img) != 6912:
        raise RuntimeError(name + ': invalid ZX Spectrum screen')
    dest = OUT / category / (name + '.png')
    dest.parent.mkdir(parents=True, exist_ok=True)
    rvm.write_png(img, str(dest), border)
    print('RVM', name, runner.why, '->', dest.relative_to(ROOT), flush=True)


def run_pair(names, target=3000):
    opt = rvm.Options()
    opt.bg = [(str(BIN / (n + '.ssx')), []) for n in names]
    opt.headless = True
    runner = rvm.Runner(opt)
    runner.start()
    if len(runner.session.jobs) < 2:
        raise RuntimeError('multitask jobs not scheduled: ' + ','.join(names))
    jobs = runner.session.jobs[-2:]
    selected = None
    best = -1
    for frame in range(target + 1500):
        runner.frame()
        if any(job.started is None for job in jobs):
            continue
        if any(job.ended is not None for job in jobs):
            break
        if frame % 50:
            continue
        picture = runner.session.m.screen()
        # Prefer meaningful drawing coverage while both jobs and shell run.
        score = sum(bool(b) for b in picture[:6144])
        if score > best and frame >= 200:
            selected = (picture, runner.session.m.border, frame)
            best = score
    if selected is None:
        raise RuntimeError('both applications were not live together: ' + ','.join(names))
    out = OUT / 'multitask' / ('-'.join(names) + '-shell.png')
    out.parent.mkdir(parents=True, exist_ok=True)
    rvm.write_png(selected[0], str(out), selected[1])
    print('RVM multitask', '+'.join(names), 'frame', selected[2], flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--only', default='')
    p.add_argument('--frames', type=int, default=1500)
    args = p.parse_args()
    only = set(args.only.split(',')) if args.only else None
    found = set()
    failures = []
    for name, category, config in captures():
        if only is not None and name not in only:
            continue
        found.add(name)
        try:
            run_one(name, category, config, args.frames)
        except Exception as exc:
            print('RVM FAIL:', name, exc, file=sys.stderr)
            failures.append(name)
    for names in PAIRS:
        identifier = '-'.join(names)
        if only is None or identifier in only:
            try:
                run_pair(names)
            except Exception as exc:
                print('RVM FAIL:', identifier, exc, file=sys.stderr)
                failures.append(identifier)
    if only is not None and not only <= found | {'-'.join(p) for p in PAIRS}:
        failures.append('unknown program(s): ' + ','.join(sorted(only-found-{'-'.join(p) for p in PAIRS})))
    count = write_gallery(OUT, 'RVM — ZX-UX kernel')
    if count != 63:
        failures.append('expected 63 RVM images, got %d' % count)
    print('RVM captured', count, 'images; failures:', len(failures))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
