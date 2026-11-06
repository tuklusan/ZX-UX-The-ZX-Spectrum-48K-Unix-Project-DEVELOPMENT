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
    'rfc': [p.stem for p in sorted((DIST / 'assets/forth-bin/ssx').glob('*.ssx'))],
    'rpc': [
        'fibopt',
        'fiblarge',
        'fibarray',
        'bases', 'burkadj', 'burkcopy', 'burkcum',
        'burkdot', 'burkflip', 'burkgcd', 'burkl1',
        'burkl2', 'burkmean', 'burkmin', 'burkmm',
        'burkprime', 'burkreal', 'burkrsrt', 'burkscale',
        'burksort', 'burkvar', 'burkvec', 'machar',
        'factorial', 'prime',
    ],
    'rfortranc': [
        'f77s_burkadj', 'f77s_burkcopy', 'f77s_burkcum', 'f77s_burkdot',
        'f77s_burkflip', 'f77s_burkgcd', 'f77s_burkl1', 'f77s_burkl2',
        'f77s_burkmean', 'f77s_burkmin', 'f77s_burkmm', 'f77s_burkprime',
        'f77s_burkreal', 'f77s_burkrsrt', 'f77s_burkscale', 'f77s_burksort',
        'f77s_burkvar', 'f77s_burkvec', 'bases', 'factorial', 'f77s_machar', 'prime',
        'na_bisect', 'na_brent', 'na_cholesky', 'na_euler',
        'na_fft', 'na_gauss', 'na_gemm', 'na_jacobi',
        'na_lcg', 'na_lupivot', 'na_machar', 'na_minilin',
        'na_newton', 'na_polyfit', 'na_rk4', 'na_romberg',
        'na_simpson', 'na_square', 'na_thomas', 'na_whet',
    ],
}
# Per-compiler capture recipes use the same runs.json as C48.
CAPTURE = json.loads((ROOT / 'build/tools/runs.json').read_text())

SOURCES = {
    'rfc': 'assets/forth-bin/ssx',
    'rpc': 'assets/pascal-bin/samples/ssx',
    'rfortranc': 'assets/fortran-bin/samples/ssx',
}
LABEL_PREFIX = {'rfc': 'FTH', 'rpc': 'PAS', 'rfortranc': 'F77'}


def label_for(compiler, index):
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
        '<h1>ZX-UX %s — %s</h1><p>Real ZX-UX executable captures from sample programs.</p>' % (escape(compiler), escape(engine.upper())),
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
    import zxscreen
    from capture_quality import program_output_lines

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
        shell_screen = bytes(runner.session.m.screen())
        shell_text = zxscreen.screen_text(shell_screen)
        chosen, best, live_frames = None, (-1, -1, -1), 0
        for frame in range(frames + 3000):
            runner.frame()
            if runner.fg and runner.fg.started is not None:
                live_frames += 1
                owned = runner.session.program_screen(runner.fg)
                picture = owned or (runner.session.m.screen(), runner.session.m.border)
                if picture and len(picture[0]) == 6912 and live_frames >= (1 if compiler == 'rfc' else 3):
                    image = bytes(picture[0])
                    rows = zxscreen.screen_text(image)
                    output = program_output_lines(rows, shell_text)
                    # The tty keeps its old login banner and loading line.
                    # A new program row or a changed owned display is required.
                    if not output and not (owned is not None and image != shell_screen):
                        continue
                    ink = sum(bool(b) for b in image[:6144])
                    score = (int('DONE ' in rows), len(output), ink)
                    if ink > 0 and score > best:
                        chosen, best = (image, picture[1]), score
            if runner.check(limit=frames):
                break
        if runner.fg is None or runner.fg.started is None or chosen is None:
            raise RuntimeError('ZX-UX process display was not observed: ' + name)
        output = DIST / 'screenshots' / compiler / 'rvm' / (name + '.png')
        output.parent.mkdir(parents=True, exist_ok=True)
        rvm.write_png(chosen[0], str(output), chosen[1])
        print(compiler, 'RVM', name, 'result rows/ink', best, flush=True)


def fuse_config(compiler, name, label, source, wait):
    """Apply project-owned run settings after compiler timing defaults."""
    config = {
        'programs': {label: source},
        'capture_delay': 0.0,
        'fuse_wait': wait,
        'sample_step': .02,
    }
    if compiler in ('rfc', 'rpc'):
        config.update(type_key_pause=.12, capture_delay=0.0,
                      fuse_wait=12.0, sample_step=.04,
                      post_command_wait=0.0, enter_pause=.1,
                      early_capture=True)
        config['reference'] = DIST / 'screenshots' / compiler / 'rvm' / (name + '.png')
    if compiler == 'rfc':
        # Compare live console rows against the separately captured RVM output.
        # Allow full tape loading and short-lived output on a slow emulator.
        config.update(type_key_pause=.25, enter_pause=.25,
                      fuse_wait=90.0, sample_step=.10,
                      console_reference=True, stop_on_reference_match=True)
    if compiler == 'rfortranc':
        config.update(fuse_speed=200, capture_delay=0.0,
                      console_output=True, early_capture=False,
                      fuse_wait=9.0, sample_step=.15,
                      enter_pause=.12, post_command_wait=0.0)
    config.update(CAPTURE.get(compiler + ':' + name, {}))
    return config


def capture_fuse(compiler, name, label, source, args, number):
    from fuse_portfolio import run_case
    local = argparse.Namespace(**vars(args))
    local.display = args.display + number + 1
    dest = DIST / 'screenshots' / compiler / 'fuse' / (name + '.png')
    run_case((label,), dest, local, fuse_config(compiler, name, label, source, args.wait))


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
    parser.add_argument('--jobs', type=int, default=8)
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
    selected = ((args.compiler,) if args.compiler else tuple(SAMPLES))
    if any(not SAMPLES[name] for name in selected):
        raise RuntimeError('No compiled programs found for selected compiler')
    tasks = list(cases(set(selected)))
    if args.engine == 'rvm':
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(capture_rvm, compiler, name, label, source, args.frames)
                       for compiler, name, label, source in tasks]
            for future in concurrent.futures.as_completed(futures):
                future.result()
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
