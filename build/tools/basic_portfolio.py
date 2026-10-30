#!/usr/bin/env python3
"""Capture actual ZX-UX BASIC SSX screens in RVM, never archival tape pictures."""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
sys.path[:0] = [str(DIST / 'sdk/bin/py'), str(ROOT / 'src/zx-ux-sdk/tools')]
from basicpack import tape_name
import rvm
from zxscreen import screen_text


def cases():
    root = DIST / 'assets/basic-bin'
    for collection in sorted(root.iterdir()) if root.is_dir() else ():
        if not collection.is_dir():
            continue
        for ssx in sorted((collection / 'ssx').glob('*.ssx')):
            original = DIST / 'assets/basic-src' / collection.name / ssx.stem
            if not (original / (ssx.stem + '.bas')).is_file():
                raise RuntimeError('missing original BASIC source: ' + ssx.stem)
            yield collection.name, ssx, tape_name(ssx.stem)


def write_gallery(out: Path, engine: str):
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<title>ZX-UX BASIC — %s</title>' % escape(engine),
             '<h1>ZX-UX BASIC — %s</h1>' % escape(engine),
             '<p>Native ZX-UX program screens; a screen alone is not gameplay verification.</p>']
    count = 0
    for collection in sorted(p for p in out.iterdir() if p.is_dir()) if out.is_dir() else ():
        parts.append('<h2>%s</h2>' % escape(collection.name))
        for png in sorted(collection.glob('*.png')):
            rel = collection.name + '/' + png.name
            original = DIST / 'assets/basic-src' / collection.name / png.stem
            links = []
            for suffix in ('.bas', '.tzx'):
                source = original / (png.stem + suffix)
                if source.is_file():
                    href = quote(__import__('os').path.relpath(source, out).replace('\\', '/'), safe='/')
                    links.append('<a href="%s">%s</a>' % (escape(href, quote=True), suffix[1:].upper()))
            parts.append('<figure><a href="%s"><img src="%s" alt="%s" width="320"></a>'
                         '<figcaption>%s — %s</figcaption></figure>' %
                         (escape(rel, quote=True), escape(rel, quote=True), escape(png.stem),
                          escape(png.stem), ' · '.join(links)))
            count += 1
    parts.append('<footer>%d native captures</footer></html>' % count)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    return count


def run_one(collection: str, ssx: Path, label: str, frames: int):
    # RVM takes its /dev/cassette/ name from the supplied filename.
    # Use precisely the short, checked rtap name, never the long game title.
    with tempfile.TemporaryDirectory(prefix='zxux-basic-rvm-') as temporary:
        alias = Path(temporary) / (label + '.ssx')
        shutil.copyfile(ssx, alias)
        if alias.read_bytes() != ssx.read_bytes():
            raise RuntimeError('RVM input changed')
        opt = rvm.Options()
        opt.prog = str(alias)
        opt.headless = True
        runner = rvm.Runner(opt)
        runner.start()
        selected = None
        best = -1
        for frame in range(frames + 3000):
            runner.frame()
            job = runner.fg
            if job.started is not None:
                picture = runner.session.program_screen(job)
                if picture and (selected is None or frame % 10 == 0):
                    pixels, border = picture
                    # Select an actual process-owned display, not the loader or shell.
                    score = sum(bool(v) for v in pixels[:6144])
                    if score > best:
                        selected, best = (bytes(pixels), border), score
            reason = runner.check(limit=frames)
            if reason:
                runner.why = reason
                break
        if runner.fg.started is None or selected is None:
            raise RuntimeError('no independently observed native process screen: ' + ssx.name)
        image, border = selected
        if len(image) != 6912:
            raise RuntimeError('invalid Spectrum screen')
        out = DIST / 'screenshots/rvm/basic' / collection / (ssx.stem + '.png')
        out.parent.mkdir(parents=True, exist_ok=True)
        rvm.write_png(image, str(out), border)
        if best < 8:
            print('BASIC RVM WARNING:', ssx.stem,
                  'Screenshot captured successfully, but automatic visual '
                  'validation did not show expected results; '
                  'manual verification required: low screen ink coverage',
                  file=sys.stderr, flush=True)
        print('BASIC RVM', ssx.stem, runner.why, 'ink', best, flush=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--only', default='')
    p.add_argument('--frames', type=int, default=1500)
    args = p.parse_args(argv)
    wanted = set(args.only.split(',')) if args.only else None
    found, failures = set(), []
    for collection, ssx, label in cases():
        if wanted is not None and ssx.stem not in wanted:
            continue
        found.add(ssx.stem)
        try:
            run_one(collection, ssx, label, args.frames)
        except Exception as e:
            print('BASIC RVM FAIL:', ssx.stem, str(e), file=sys.stderr, flush=True)
            failures.append(ssx.stem)
    if wanted is not None:
        failures.extend(sorted(wanted - found))
    out = DIST / 'screenshots/rvm/basic'
    count = write_gallery(out, 'RVM')
    if wanted is None and count != len(found):
        failures.append('incomplete BASIC RVM gallery')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
