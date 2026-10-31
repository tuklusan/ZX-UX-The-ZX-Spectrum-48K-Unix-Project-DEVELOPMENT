#!/usr/bin/env python3
"""Small, genuine ZX-UX executable galleries for the other SDK compilers."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from html import escape
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
sys.path[:0] = [str(DIST / 'sdk/bin/py'), str(Path(__file__).resolve().parent)]

SAMPLES = {
    'rb2ct': ['minelay', 'galaxian', 'invaders'],
    'rfc': [
        'bisect', 'brentrot', 'cholesky', 'eulerode', 'gauss1d', 'gemm8bit',
        'jacrelx', 'lcgrand', 'lupivot', 'machar', 'minilin', 'newton',
        'polyfit', 'rk4fixed', 'romberg', 'simpson', 'square', 'thomastr',
        'tinyfft', 'whetston', 'calendar', 'pfbench', 'pfsieve',
        'hufdemo', 'worms',
    ],
    'rpc': [
        'recovered_course_030_fibonacci_optimized',
        'recovered_course_040_fibonacci_large',
        'recovered_21_fibonacci_array',
        'bases', 'f77s_burkadj', 'f77s_burkcopy', 'f77s_burkcum',
        'f77s_burkdot', 'f77s_burkflip', 'f77s_burkgcd', 'f77s_burkl1',
        'f77s_burkl2', 'f77s_burkmean', 'f77s_burkmin', 'f77s_burkmm',
        'f77s_burkprime', 'f77s_burkreal', 'f77s_burkrsrt', 'f77s_burkscale',
        'f77s_burksort', 'f77s_burkvar', 'f77s_burkvec', 'f77s_machar',
        'factorial', 'prime',
    ],
    'rfortranc': [
        'f77s_burkadj', 'f77s_burkcopy', 'f77s_burkcum', 'f77s_burkdot',
        'f77s_burkflip', 'f77s_burkgcd', 'f77s_burkl1', 'f77s_burkl2',
        'f77s_burkmean', 'f77s_burkmin', 'f77s_burkmm', 'f77s_burkprime',
        'f77s_burkreal', 'f77s_burkrsrt', 'f77s_burkscale', 'f77s_burksort',
        'f77s_burkvar', 'f77s_burkvec', 'bases', 'factorial', 'f77s_machar', 'prime',
    ],
}
# Per-compiler capture recipes use the same runs.json as C48.
CAPTURE = json.loads((ROOT / 'build/tools/runs.json').read_text())

SOURCES = {
    'rb2ct': 'assets/rb2ct-bin/ssx',
    'rfc': 'assets/forth-bin/ssx',
    'rpc': 'assets/pascal-bin/showcase/ssx',
    'rfortranc': 'assets/fortran-bin/showcase/ssx',
}
LABEL_PREFIX = {'rfc': 'FTH', 'rpc': 'PAS', 'rfortranc': 'F77'}
RB2CT_LABELS = ('MINE', 'GALAX', 'INVA')


def label_for(compiler, index):
    if compiler == 'rb2ct':
        return RB2CT_LABELS[index]
    return '%s%02d' % (LABEL_PREFIX[compiler], index + 1)


def cases(compilers=None):
    for compiler, group in SAMPLES.items():
        if compilers is not None and compiler not in compilers:
            continue
        for index, name in enumerate(group):
            source = DIST / SOURCES[compiler] / (name + '.ssx')
            if not source.is_file():
                raise FileNotFoundError('missing ' + compiler + ' executable: ' + str(source))
            yield compiler, name, label_for(compiler, index), source


def write_gallery(compiler, engine):
    output = DIST / 'screenshots' / compiler / engine
    items = SAMPLES[compiler]
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>ZX-UX %s — %s</title>' % (escape(compiler), escape(engine.upper())),
        '<style>body{font:16px system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;background:#121212;color:#eee}figure{display:inline-block;vertical-align:top;margin:0 16px 24px 0}img{width:320px;image-rendering:pixelated}a{color:#9cf}</style>',
        '<h1>ZX-UX %s — %s</h1><p>Real ZX-UX executable captures from curated showcase programs.</p>' % (escape(compiler), escape(engine.upper())),
    ]
    for name in items:
        png = output / (name + '.png')
        if not png.is_file() or png.stat().st_size == 0:
            raise FileNotFoundError('missing capture: ' + str(png))
        link = quote(os.path.relpath(DIST / SOURCES[compiler] / (name + '.ssx'), output).replace(os.sep, '/'), safe='/')
        rel = quote(png.name, safe='')
        parts.append(
            '<figure><a href="%s"><img src="%s" alt="%s" loading="lazy"></a><figcaption>%s · <a href="%s">SSX</a></figcaption></figure>'
            % (rel, rel, escape(name, quote=True), escape(name), escape(link, quote=True))
        )
    parts.append('<footer>%d real captures</footer></html>' % len(items))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'index.html').write_text('\n'.join(parts) + '\n', encoding='utf-8')


def capture_rvm(compiler, name, label, source, frames):
    import rvm

    with tempfile.TemporaryDirectory(prefix='zxux-' + compiler + '-') as tmp:
        alias = Path(tmp) / (label + '.ssx')
        shutil.copyfile(source, alias)
        if alias.read_bytes() != source.read_bytes():
            raise RuntimeError('SSX input changed during capture')
        options = rvm.Options()
        options.prog = str(alias)
        options.headless = True
        runner = rvm.Runner(options)
        runner.start()
        chosen, best, live_frames = None, -1, 0
        for frame in range(frames + 3000):
            runner.frame()
            if runner.fg and runner.fg.started is not None:
                live_frames += 1
                if compiler == 'rb2ct' and frame % 10:
                    pass  # A longer-running graphical game needs sampling.
                else:
                    picture = runner.session.program_screen(runner.fg)
                    if picture is None and compiler == 'rfc':
                        picture = runner.picture()
                    if picture and len(picture[0]) == 6912 and live_frames >= (1 if compiler == 'rfc' else 3):
                        score = sum(bool(b) for b in picture[0][:6144])
                        if (compiler == 'rb2ct' and score > best or compiler != 'rb2ct' and score > 0):
                            chosen, best = (bytes(picture[0]), picture[1]), score
            if runner.check(limit=frames):
                break
        if runner.fg is None or runner.fg.started is None or chosen is None:
            raise RuntimeError('ZX-UX process display was not observed: ' + name)
        output = DIST / 'screenshots' / compiler / 'rvm' / (name + '.png')
        output.parent.mkdir(parents=True, exist_ok=True)
        rvm.write_png(chosen[0], str(output), chosen[1])
        print(compiler, 'RVM', name, 'ink', best, flush=True)


def capture_fuse(compiler, name, label, source, args, number):
    from fuse_portfolio import run_case

    local = argparse.Namespace(**vars(args))
    local.display = args.display + number + 1
    dest = DIST / 'screenshots' / compiler / 'fuse' / (name + '.png')
    config = {
        'programs': {label: source},
        'capture_delay': 1.0 if compiler == 'rb2ct' else 0.0,
        'fuse_wait': args.wait,
        'sample_step': .2 if compiler == 'rb2ct' else .02,
    }
    config.update(CAPTURE.get(compiler + ':' + name, {}))
    if compiler == 'rfortranc':
        # The genuine tape loader can take several seconds before FORTRAN
        # starts. Sample beyond that, including its 100-tick output hold.
        config.update(fuse_wait=12.0, sample_step=.08,
                      enter_pause=.12, post_command_wait=0.0)
    if compiler in ('rfc', 'rpc', 'rfortranc'):
        config['reference'] = DIST / 'screenshots' / compiler / 'rvm' / (name + '.png')
        config.setdefault('early_capture', True)
    run_case((label,), dest, local, config)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', required=True, choices=['rvm', 'fuse'])
    parser.add_argument('--compiler', choices=tuple(SAMPLES))
    parser.add_argument('--frames', type=int, default=1500)
    parser.add_argument('--fuse', type=Path)
    parser.add_argument('--assets', type=Path)
    parser.add_argument('--rom', type=Path, default=ROOT / 'src/zx-ux/rom/48.rom')
    parser.add_argument('--libdir', type=Path)
    parser.add_argument('--display', type=int, default=600)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--wait', type=int, default=8)
    parser.add_argument('--boot-wait', type=int, default=90)
    parser.add_argument('--speed', type=int, default=100)
    parser.add_argument('--multitask-wait', type=int, default=60)
    args = parser.parse_args(argv)
    if args.engine == 'fuse' and (not args.fuse or not args.assets):
        parser.error('--fuse and --assets required for Fuse')
    if not 1 <= args.jobs <= 16:
        parser.error('--jobs must be 1..16')
    for attr in ('fuse', 'rom', 'assets', 'libdir'):
        value = getattr(args, attr)
        if value is not None:
            setattr(args, attr, value.resolve())
    # Sparse FORTRAN output cannot yet be verified reliably in Fuse.
    selected = ((args.compiler,) if args.compiler else
                ('rb2ct', 'rfc', 'rpc') if args.engine == 'fuse' else tuple(SAMPLES))
    tasks = list(cases(set(selected)))
    if args.engine == 'rvm':
        for compiler, name, label, source in tasks:
            capture_rvm(compiler, name, label, source, args.frames)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(capture_fuse, *case, args, index) for index, case in enumerate(tasks)]
            for future in concurrent.futures.as_completed(futures):
                future.result()
    for compiler in selected:
        write_gallery(compiler, args.engine)
    return 0


if __name__ == '__main__':
    sys.exit(main())
