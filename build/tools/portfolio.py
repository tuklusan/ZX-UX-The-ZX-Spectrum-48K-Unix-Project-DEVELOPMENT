#!/usr/bin/env python3
"""Capture the built C48 portfolio from the real ZX-UX kernel in RVM.

Usage: python3 build/tools/portfolio.py [--only NAME[,NAME]] [--frames N]
No C48 programs are recompiled. The two multitasking scenes are included.
"""
import argparse
import json
import os
import sys
from html import escape
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
sys.path[:0] = [str(DIST / 'sdk/bin/py'), str(Path(__file__).resolve().parent)]
import rvm
import zxscreen
import zxux
from gallery import write_gallery

SOURCES = DIST / 'assets/c48-src'
BIN = DIST / 'assets/c48-bin/ssx'
OUT = DIST / 'screenshots/rvm'
PAIRS = (('hanoi', 'queens8'), ('mobius', 'torus'))
# Captures run graphics to completion rather than using the test suite's
# short two-frame animation argument. Other programs retain test inputs.
CAPTURE = {
    'galaxy': {'args': [], 'frames': 3200, 'fuse_wait': 45, 'fuse_speed': 300},
    # Render exactly one full scene and capture its real exit screen.
    # A running multi-scene demo can be caught halfway through clearing/redrawing.
    'goblet': {'args': ['1'], 'frames': 4400, 'require_exit': True},
    'julia': {'args': [], 'frames': 30000, 'fuse_wait': 270, 'fuse_speed': 300, 'first_fractal': True},
    'mandel': {'args': [], 'frames': 30000, 'fuse_wait': 270, 'fuse_speed': 300, 'first_fractal': True},
    'mobius': {'args': ['1'], 'frames': 4400, 'require_exit': True},
    'torus': {'args': [], 'frames': 5500, 'fuse_wait': 55, 'fuse_speed': 300},
    'kaleido': {'args': [], 'frames': 3600, 'fuse_wait': 20},
    'ball': {'args': [], 'frames': 1100, 'fuse_wait': 12},
    # Capture live gameplay while shields are still visible; waiting until the
    # game has nearly finished can legitimately produce a monochrome screen.
    'invaders': {'args': [], 'keys': 'm', 'keygap': 160,
                 'frames': 900, 'fuse_wait': 15},
    # Override tests/sdk/runs.json quiz:play; do not answer all ten questions.
    'quiz': {'keys': '', 'frames': 1200, 'expect_text': 'Question:'},
    # The intro flushes keys. Press Q only after the displayed intro is idle.
    '3dpaint': {'keys': '', 'frames': 3200, 'start_on_idle': 'q',
                'expect_gameplay': True},
}


def invaders_live_score(scr):
    """Prefer live gameplay with green shields and a visible alien formation."""
    rows = zxscreen.rgb_rows(scr)
    green = 0
    red = 0
    black = 0
    for y in range(56, 184):
        row = rows[y]
        for x in range(56, 264):
            i = x * 3
            r, g, b = row[i], row[i + 1], row[i + 2]
            if g > 120 and g > r + 40 and g > b + 40:
                green += 1
            elif r > 120 and r > g + 40 and r > b + 40:
                red += 1
            elif y < 150 and r < 32 and g < 32 and b < 32:
                black += 1
    # Ignore boot/blank/monochrome frames; live gameplay with intact shields
    # has a conspicuous green pixel population.
    if green < 1000:
        return 0
    return green * 8 + red * 4 + black


def captures():
    configured = json.loads((ROOT / 'build/tools/runs.json').read_text())
    scenarios = {}
    for name, run in configured.items():
        base = name.split(':', 1)[0]
        if base not in scenarios or ':' in name and 'keys' in run and 'keys' not in scenarios[base]:
            scenarios[base] = run
    for source in sorted(SOURCES.glob('*/*.c')):
        if source.stem == 'seckern':  # deliberately un-compilable security fixture
            continue
        name = source.stem
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
    intro_previous = None
    intro_idle_frames = 0
    intro_started = False
    live_capture = None
    live_score = -1
    for frame_index in range(budget + 3000):
        runner.frame()
        if name == 'invaders' and runner.fg.started is not None and frame_index % 5 == 0:
            candidate, candidate_border = runner.picture()
            score = invaders_live_score(candidate)
            if score > live_score:
                live_capture = (candidate, candidate_border)
                live_score = score
        if config.get('start_on_idle') and not intro_started and runner.fg.started is not None:
            # Wait for an unchanged, nonblank intro; no hard-coded boot frame.
            # Inject keys only after the game's own input flush has finished.
            screen, _ = runner.picture()
            if screen == intro_previous and sum(bool(b) for b in screen[:6144]) > 160:
                intro_idle_frames += 1
            else:
                intro_idle_frames = 0
            intro_previous = screen
            if intro_idle_frames >= 35:
                runner.session.kb.add(zxux.parse_keys(config['start_on_idle']))
                intro_started = True
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
    if config.get('require_exit') and runner.why != 'exit':
        raise RuntimeError(name + ': complete scene was not reached (' + str(runner.why) + ')')
    if config.get('start_on_idle') and not intro_started:
        raise RuntimeError(name + ': intro was not ready for a scripted key')
    if name == 'invaders' and live_capture is not None and live_score > 0:
        img, border = live_capture
    else:
        img, border = runner.picture()
    if len(img) != 6912:
        raise RuntimeError(name + ': invalid ZX Spectrum screen')
    if config.get('expect_text') and config['expect_text'] not in zxscreen.screen_text(img):
        raise RuntimeError(name + ': expected screen text missing: ' + config['expect_text'])
    if config.get('expect_gameplay'):
        # Gameplay tiles use colored paper; the instruction screen does not.
        if not any(((a >> 3) & 7) in (3, 4, 5, 6) for a in img[6144:]):
            raise RuntimeError(name + ': still on intro, not the game board')
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


def add_source_links():
    """Write relative C source links into *RVM's* freshly built gallery only.

    Recomputed every run: copying release/dist to another repository keeps
    the links working without embedding a GitHub owner, branch, or SHA.
    """
    index = OUT / 'index.html'
    lines = index.read_text(encoding='utf-8').splitlines(keepends=True)
    sources = {}
    for path in sorted(SOURCES.glob('*/*.c')):
        name = path.stem
        sources[f'{path.parent.name}/{name}.png'] = [path]
    for a, b in PAIRS:
        sources[f'multitask/{a}-{b}-shell.png'] = [SOURCES / 'demos' / (n + '.c') for n in (a, b)]
    for i, line in enumerate(lines):
        for png, paths in sources.items():
            if f'<a href="{png}"' not in line:
                continue
            links = []
            for source in paths:
                if source.is_file():
                    href = quote(os.path.relpath(source, OUT).replace(os.sep, '/'), safe='/')
                    links.append(f'<a href="{escape(href, quote=True)}">C source: {escape(source.name)}</a>')
            if links:
                lines[i] = line.replace('</figcaption>', ' — ' + ', '.join(links) + '</figcaption>')
            break
    index.write_text(''.join(lines), encoding='utf-8')


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
    add_source_links()
    if count != 63:
        failures.append('expected 63 RVM images, got %d' % count)
    print('RVM captured', count, 'images; failures:', len(failures))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
