#!/usr/bin/env python3
"""Final release screenshot layout and source/binary link generation."""
from __future__ import annotations
from html import escape
from pathlib import Path
from urllib.parse import quote
import os

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
ASSETS = DIST / 'assets'
SHOTS = DIST / 'screenshots'
# Capture tools retain their internal names; final release uses asset bin names.
LAYOUT = {'c48': 'c48-bin', 'rbc': 'rbc-bin', 'rfc': 'forth-bin',
          'rpc': 'pascal-bin', 'rfortranc': 'fortran-bin'}
SRC = {'c48-bin': ('c48-src', '.c'), 'rbc-bin': ('rbc-src', '.bas'),
       'forth-bin': ('forth-src', '.fth'), 'pascal-bin': ('pascal-src', '.pas'),
       'fortran-bin': ('fortran-src', '.f')}
DOUBLE = {'hanoi-queens8-shell': ('hanoi', 'queens8'),
          'mobius-torus-shell': ('mobius', 'torus')}


def rel(url: Path, parent: Path) -> str:
    return quote(os.path.relpath(url, parent).replace(os.sep, '/'), safe='/')


def source_lookup(category: str):
    folder, extension = SRC[category]
    source = ASSETS / folder
    found = {}
    if category == 'rbc-bin':
        # The selected compilation listing lives in rbc-src. The gallery
        # links every unmodified original listing and cassette in basic-src.
        for game in sorted((ASSETS / 'basic-src').glob('*/*')):
            if not game.is_dir():
                continue
            originals = sorted(p for p in game.iterdir()
                               if p.is_file() and p.suffix.lower() in ('.bas', '.tzx'))
            if originals:
                found[(game.parent.name, game.name)] = originals
        return found
    for p in source.rglob('*' + extension):
        if p.stem in found:
            raise RuntimeError(f'Duplicate source identifier: {category} {p.stem}')
        found[p.stem] = [p]
    return found


def pictures_in(directory: Path):
    return set(directory.rglob('*.png')) if directory.is_dir() else set()


def finalize():
    for former, actual in LAYOUT.items():
        old, new = SHOTS / former, SHOTS / actual
        if old.exists():
            if new.exists():
                raise RuntimeError('Both screenshot layouts exist: ' + str(new))
            old.rename(new)
    # Empty compiler placeholder has no programs or screenshots yet.
    (SHOTS / 'rb2ct-bin').mkdir(parents=True, exist_ok=True)
    (SHOTS / 'rb2ct-bin/.gitkeep').touch()

    for category in SRC:
        root = ASSETS / category
        shots = SHOTS / category
        if not root.is_dir() or not shots.is_dir():
            raise RuntimeError('Missing asset or screenshot directory: ' + category)
        source_map = source_lookup(category)
        expected = {'rvm': set(), 'fuse': set()}
        images = {'rvm': {}, 'fuse': {}}
        executable_sources = {}
        bins = set()
        for ssx in sorted(root.rglob('*.ssx')):
            key = (ssx.parent.parent.name, ssx.stem) if category == 'rbc-bin' else ssx.stem
            cassette = ssx.parent.parent / 'tzx' / (ssx.stem + '.tzx')
            if not cassette.is_file():
                raise RuntimeError('Missing TZX companion: ' + str(ssx))
            if key in executable_sources:
                raise RuntimeError('Duplicate executable: ' + str(key))
            originals = source_map.get(key)
            if not originals or not all(src.is_file() for src in originals):
                raise RuntimeError('Missing source for executable: ' + str(key))
            executable_sources[key] = (ssx, cassette, originals)
            bins.add(key)
            if category == 'c48-bin':
                short = originals[0].relative_to(ASSETS / 'c48-src').parent.as_posix() + '/' + ssx.stem + '.png'
            elif isinstance(key, tuple):
                short = key[0] + '/' + ssx.stem + '.png'
            else:
                short = ssx.stem + '.png'
            for engine in expected:
                pic = shots / engine / short
                if not pic.is_file():
                    raise RuntimeError(f'Missing {engine} screenshot for {category}: {short}')
                expected[engine].add(pic)
                images[engine][pic] = [(key, ssx, cassette, originals)]

        if category == 'c48-bin':
            for name, members in DOUBLE.items():
                group = []
                for member in members:
                    if member not in executable_sources:
                        raise RuntimeError('Multitask source missing: ' + member)
                    ssx, cassette, originals = executable_sources[member]
                    group.append((member, ssx, cassette, originals))
                for engine in expected:
                    pic = shots / engine / 'multitask' / (name + '.png')
                    if not pic.is_file():
                        raise RuntimeError('Missing multitask screenshot: ' + str(pic))
                    expected[engine].add(pic)
                    images[engine][pic] = group

        for engine in expected:
            actual = pictures_in(shots / engine)
            if actual != expected[engine]:
                missing = expected[engine] - actual
                unexpected = actual - expected[engine]
                raise RuntimeError(f'{category}/{engine}: missing {len(missing)} extra {len(unexpected)}')
            gallery = shots / engine
            parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
                     '<meta name="viewport" content="width=device-width,initial-scale=1">',
                     f'<title>ZX-UX {escape(category)} — {engine.upper()}</title>',
                     '<style>body{font:16px system-ui,sans-serif;background:#151515;color:#eee;max-width:1100px;margin:2em auto}a{color:#9cf}figure{display:inline-block;vertical-align:top;margin:12px;width:320px}img{width:320px;image-rendering:pixelated}</style>',
                     f'<h1>{escape(category)} — {engine.upper()}</h1>']
            for pic in sorted(expected[engine]):
                img_url = rel(pic, gallery)
                links = []
                for key, ssx, tzx, originals in images[engine][pic]:
                    # Both release forms and every original belong below the image.
                    for other in (ssx, tzx):
                        links.append(f'<a href="{escape(rel(other, gallery), quote=True)}">{escape(other.suffix[1:].upper())}</a>')
                    for src in originals:
                        links.append(f'<a href="{escape(rel(src, gallery), quote=True)}">{escape(src.name)}</a>')
                parts.append(f'<figure><a href="{escape(img_url, quote=True)}">'
                             f'<img src="{escape(img_url, quote=True)}" alt="{escape(pic.stem, quote=True)}" loading="lazy"></a>'
                             f'<figcaption>{escape(pic.stem)} — {" · ".join(links)}</figcaption></figure>')
            parts.append(f'<footer>{len(expected[engine])} screenshots</footer></html>')
            (gallery / 'index.html').write_text('\n'.join(parts) + '\n', encoding='utf-8')
        print(f'PASS {category}: {len(bins)} SSX/TZX programs and both screenshot sets')


if __name__ == '__main__':
    finalize()
