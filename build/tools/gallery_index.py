#!/usr/bin/env python3
"""Single local index linking the real screenshots for each SDK compiler."""
import argparse
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = ROOT / 'dist/screenshots'
COMPILERS = (('c48', 'rcc — C48'), ('rbc', 'rbc — Sinclair BASIC'),
             ('rfc', 'rfc — Forth'), ('rpc', 'rpc — Pascal'),
             ('rfortranc', 'rfortranc — FORTRAN'))


def write_index(engines=('rvm', 'fuse')):
    complete = engines == ('rvm', 'fuse')
    if complete:
        from asset_gallery import finalize
        finalize()
    lines = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<title>ZX-UX compiler screenshots</title>',
             '<style>body{font:18px system-ui,sans-serif;max-width:820px;margin:2em auto;padding:0 1em;background:#121212;color:#eee}a{color:#9cf}li{margin:.7em 0}</style>',
             '<h1>ZX-UX compiler screenshots</h1><ul>']
    for directory, title in COMPILERS:
        if complete:
            directory = {'c48': 'c48-bin', 'rbc': 'rbc-bin',
                         'rfc': 'forth-bin', 'rpc': 'pascal-bin',
                         'rfortranc': 'fortran-bin'}[directory]
        links = []
        for engine in engines:
            index = SCREENSHOTS / directory / engine / 'index.html'
            if not index.is_file():
                raise FileNotFoundError('missing ' + str(index))
            links.append('<a href="%s/%s/index.html">%s</a>' % (directory, engine, escape(engine.upper())))
        lines.append('<li>%s: %s</li>' % (escape(title), ' · '.join(links)))
    lines += ['</ul><p>Real ZX-UX program captures; a screenshot alone does not prove every feature works.</p>', '</html>']
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    (SCREENSHOTS / 'index.html').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if complete:
        # Keep the older C48 source-link entry points alongside final galleries.
        source = ROOT / 'dist/assets/c48-src'
        for engine in engines:
            output = SCREENSHOTS / engine / 'index.html'
            output.parent.mkdir(parents=True, exist_ok=True)
            refs = ['<!doctype html><html lang="en"><meta charset="utf-8">',
                    '<title>ZX-UX C48 sources — ' + engine.upper() + '</title>']
            for file in sorted(source.rglob('*.c')):
                if (ROOT / 'dist/assets/c48-bin/ssx' / (file.stem + '.ssx')).is_file():
                    rel = file.relative_to(source).as_posix()
                    refs.append('<p><a href="../../assets/c48-src/' + rel + '">' + rel + '</a></p>')
            (output).write_text('\n'.join(refs) + '\n', encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', choices=['rvm', 'fuse'])
    args = p.parse_args()
    write_index((args.engine,) if args.engine else ('rvm', 'fuse'))
