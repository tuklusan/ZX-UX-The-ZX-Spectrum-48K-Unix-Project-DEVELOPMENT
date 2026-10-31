#!/usr/bin/env python3
"""Single local index linking the real screenshots for each SDK compiler."""
import argparse
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = ROOT / 'dist/screenshots'
COMPILERS = (('c48', 'rcc — C48'), ('rbc', 'rbc — Sinclair BASIC'),
             ('rb2ct', 'rb2ct — historical BASIC-to-C48 ports'),
             ('rfc', 'rfc — Forth'), ('rpc', 'rpc — Pascal'),
             ('rfortranc', 'rfortranc — FORTRAN'))


def write_index(engines=('rvm', 'fuse')):
    lines = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<title>ZX-UX compiler screenshots</title>',
             '<style>body{font:18px system-ui,sans-serif;max-width:820px;margin:2em auto;padding:0 1em;background:#121212;color:#eee}a{color:#9cf}li{margin:.7em 0}</style>',
             '<h1>ZX-UX compiler screenshots</h1><ul>']
    for directory, title in COMPILERS:
        links = []
        for engine in engines:
            index = SCREENSHOTS / directory / engine / 'index.html'
            if not index.is_file():
                if engine == 'fuse' and directory in ('rpc', 'rfortranc'):
                    continue  # No valid real Fuse capture for fast-exiting programs.
                raise FileNotFoundError('missing ' + str(index))
            links.append('<a href="%s/%s/index.html">%s</a>' % (directory, engine, escape(engine.upper())))
        lines.append('<li>%s: %s</li>' % (escape(title), ' · '.join(links)))
    lines += ['</ul><p>Real ZX-UX program captures; a screenshot alone does not prove every feature works.</p>', '</html>']
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    (SCREENSHOTS / 'index.html').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', choices=['rvm', 'fuse'])
    args = p.parse_args()
    write_index((args.engine,) if args.engine else ('rvm', 'fuse'))
