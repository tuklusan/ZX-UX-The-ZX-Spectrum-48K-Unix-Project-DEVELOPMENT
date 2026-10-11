#!/usr/bin/env python3
"""Screenshot gallery for C48 programs running on ZX-UX and other VMs.
Reads PNG files from build/shots and build/shots-vm, then writes
build/gallery.html with links to those images.

  python3 tools/gallery.py [results-ssxrun.txt] [results-oracle.txt]
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUNS = json.load(open(os.path.join(ROOT, 'sdk', 'tests', 'runs.json')))
SHOTS = os.path.join(ROOT, 'build', 'shots')
VM = os.path.join(ROOT, 'build', 'shots-vm')
ORDER = ['games', 'apps', 'demos', 'examples', 'sound', 'security']


def img(path, alt):
    if not os.path.exists(path):
        return '<div class="none">not compared</div>'
    rel = os.path.relpath(path, os.path.join(ROOT, 'build')).replace(os.sep, '/')
    return '<img src="%s" alt="%s" width="288" height="224" loading="lazy">' % (html.escape(rel, quote=True), html.escape(alt))


def results(path, pat):
    out = {}
    if path and os.path.exists(path):
        for l in open(path):
            m = re.match(pat, l)
            if m:
                out[m.group(1)] = l.strip()
    return out


def main(argv):
    rx = results(argv[0] if argv else None, r'(\S+)\s+(PASS|FAIL)')
    ov = results(argv[1] if len(argv) > 1 else None, r'(\S+)\s+(PASS|FAIL)')
    sizes = {}
    sj = os.path.join(ROOT, 'build', 'sizes.json')
    if os.path.exists(sj):
        sizes = {r['name']: r for r in json.load(open(sj))}
    names = sorted(RUNS, key=lambda n: (ORDER.index(RUNS[n]['dir']), n))
    cards = []
    for n in names:
        r = RUNS[n]
        f = n.replace(':', '_')
        base = n.split(':')[0]
        args = ' '.join(r.get('args', []))
        keys = r.get('keys', '')
        cmd = '/dev/cassette/%s%s' % (r.get('src', base), (' ' + args) if args else '')
        s = sizes.get(base)
        mode = ''
        if s:
            mode = '%s · needs %s bytes' % ('SSB1 bytecode' if s['mode'] == 'bytecode' else 'native Z80',
                                           format(s['bc_need'] if s['mode'] == 'bytecode' else s['native_need'], ','))
        ok_r = 'PASS' in rx.get(n, '')
        has_vm = os.path.isfile(os.path.join(VM, f + '.png'))
        has_ref = os.path.isfile(os.path.join(VM, f + '.sdk.png'))
        ok_v = has_vm and 'PASS' in ov.get(n, '')
        cards.append('''<article class="prog" id="%s">
<header><h3>%s</h3><span class="grp">%s</span>
<span class="pill %s">ZX-UX %s</span><span class="pill %s">VM %s</span></header>
<p class="cmd"><code># %s</code>%s</p>
<p class="meta">%s</p>
<div class="shots">
<figure>%s<figcaption>ZX-UX on the Spectrum, loaded from tape</figcaption></figure>
<figure>%s<figcaption>rvm, the ZX-UX SDK's VM</figcaption></figure>
<figure>%s<figcaption>Optional historical reference VM</figcaption></figure>
</div></article>''' % (
            html.escape(f), html.escape(n), html.escape(r['dir']),
            'ok' if ok_r else 'bad', 'ran' if ok_r else 'failed',
            'ok' if ok_v else ('bad' if has_vm else 'unknown'),
            ('passed' if ok_v else 'failed') if has_vm else 'not tested',
            html.escape(cmd), (' <span class="keys">keys: <code>%s</code></span>' % html.escape(keys)) if keys else '',
            html.escape(mode),
            img(os.path.join(SHOTS, f + '.ZX-UX.png'), n + ' on ZX-UX'),
            img(os.path.join(VM, f + '.png'), n + ' in rvm'),
            img(os.path.join(VM, f + '.sdk.png'), n + ' in the C48 SDK')))
    nr = sum(1 for n in names if 'PASS' in rx.get(n, ''))
    nv = sum(1 for n in names if 'PASS' in ov.get(n, ''))
    page = PAGE.replace('@CARDS@', '\n'.join(cards)).replace('@N@', str(len(names))) \
        .replace('@NR@', str(nr)).replace('@NV@', str(nv)) \
        .replace('@NP@', str(len({n.split(':')[0] for n in names})))
    out = os.path.join(ROOT, 'build', 'gallery.html')
    open(out, 'w').write(page)
    print(out, len(page))


PAGE = '''<title>ZX-UX C48 Gallery</title>
<style>
/* layout: a header strip like the Spectrum's border, then one card per program
   with three screens side by side (stacking on phones) */
:root {
  --bg: #eef0f4; --panel: #ffffff; --fg: #15171c; --muted: #5b6070;
  --rule: #d5d9e2; --accent: #0a33c8; --ok: #0d7a3a; --bad: #b3261e;
  --stripe1: #d40000; --stripe2: #d4d400; --stripe3: #00a800; --stripe4: #00b4d4;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  --body: "IBM Plex Sans", system-ui, sans-serif;
  --display: "Silkscreen", var(--mono);
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0d0f14; --panel: #161a22; --fg: #e8eaf0; --muted: #9aa1b2; --rule: #2a303c;
  --accent: #7f9bff; --ok: #4fd18b; --bad: #ff8a80; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0d0f14; --panel: #161a22; --fg: #e8eaf0; --muted: #9aa1b2; --rule: #2a303c;
  --accent: #7f9bff; --ok: #4fd18b; --bad: #ff8a80; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.5 var(--body); margin: 0; }
.wrap { max-width: 1000px; margin: 0 auto; padding-inline: 16px; padding-block: 24px 48px; }
.stripes { display: flex; height: 6px; }
.stripes i { flex: 1; } .stripes i:nth-child(1){background:var(--stripe1)} .stripes i:nth-child(2){background:var(--stripe2)}
.stripes i:nth-child(3){background:var(--stripe3)} .stripes i:nth-child(4){background:var(--stripe4)}
h1 { font: 400 28px/1.2 var(--display); margin: 20px 0 8px; letter-spacing: .02em; text-wrap: balance; }
.lede { max-width: 68ch; color: var(--muted); margin: 0 0 16px; }
.tally { display: flex; flex-wrap: wrap; gap: 8px 24px; font: 14px var(--mono); margin: 0 0 24px; font-variant-numeric: tabular-nums; }
.tally b { color: var(--fg); }
.prog { background: var(--panel); border: 1px solid var(--rule); border-radius: 6px; padding: 16px; margin-block: 0 16px; }
.prog header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 12px; }
.prog h3 { margin: 0; font: 600 17px var(--mono); }
.grp { color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: .06em; }
.pill { font: 12px var(--mono); padding: 1px 8px; border-radius: 999px; border: 1px solid currentColor; }
.pill.ok { color: var(--ok); } .pill.bad { color: var(--bad); }
.cmd, .meta { margin: 6px 0 0; font-size: 13px; color: var(--muted); overflow-wrap: anywhere; }
.cmd code, .keys code { font-family: var(--mono); color: var(--fg); }
.keys { margin-left: 12px; }
.shots { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }
figure { margin: 0; min-width: 0; }
figure img { width: 100%; height: auto; image-rendering: pixelated; display: block; border-radius: 3px; }
figcaption { font-size: 12px; color: var(--muted); margin-top: 4px; }
.none { aspect-ratio: 288 / 224; display: grid; place-items: center; border: 1px dashed var(--rule);
  color: var(--muted); font-size: 12px; border-radius: 3px; max-width: 100%; }
@media (max-width: 700px) { .shots { grid-template-columns: 1fr; } }
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&family=Silkscreen&display=swap">
<div class="stripes" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
<div class="wrap">
<h1>ZX-UX C48 Gallery</h1>
<p class="lede">The C48 SDK corpus, compiled by the ZX-UX SDK (rcc). Each program was loaded from cassette and run on ZX-UX v1 on an emulated 48K Spectrum,
and run in the independent ZX-UX VM. The third screen is present only when a separately supplied historical reference VM was used.
Four games are seeded from ticks(), which on ZX-UX is the real clock, so their ZX-UX screens show a different game.</p>
<p class="tally"><span><b>@NP@</b> programs, <b>@N@</b> sessions</span><span>ZX-UX: <b>@NR@/@N@</b> ran from tape</span><span>VM: <b>@NV@/@N@</b> independent v1 VM sessions passed</span></p>
@CARDS@
</div>
'''

if __name__ == '__main__':
    main(sys.argv[1:])
