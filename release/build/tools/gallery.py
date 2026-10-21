#!/usr/bin/env python3
"""Small offline HTML index for actual ZX-UX screenshot captures."""
from html import escape
from pathlib import Path

CATEGORIES = ('apps', 'demos', 'examples', 'games', 'security', 'sound', 'multitask')


def write_gallery(destination: Path, engine: str):
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>ZX-UX C48 — %s</title>' % escape(engine),
             '<style>body{font:16px system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;background:#121212;color:#eee}',
             'section{display:flex;flex-wrap:wrap;gap:18px}figure{margin:0 0 1.2em;width:320px}',
             'img{width:320px;height:auto;image-rendering:pixelated;background:black}figcaption{margin-top:.4em}</style>',
             '<h1>ZX-UX C48 — %s</h1><p>Fresh captures from the real ZX-UX kernel.</p>' % escape(engine)]
    count = 0
    for cat in CATEGORIES:
        pictures = sorted((destination / cat).glob('*.png'))
        if not pictures:
            continue
        parts.extend(('<h2>%s</h2>' % escape(cat.title()), '<section>'))
        for p in pictures:
            relative = f'{cat}/{p.name}'
            parts.append('<figure><a href="%s"><img src="%s" loading="lazy" alt="%s"></a><figcaption>%s</figcaption></figure>' %
                         (escape(relative), escape(relative), escape(p.stem), escape(p.stem)))
            count += 1
        parts.append('</section>')
    parts.extend(('<footer>%d actual screenshots</footer>' % count, '</html>'))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'index.html').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    return count
