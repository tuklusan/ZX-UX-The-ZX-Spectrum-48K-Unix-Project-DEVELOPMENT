#!/usr/bin/env python3
"""Native and bytecode sizes of every C48 corpus program -> build/sizes.json
and the rows of SPEC-SDK-R2 section 9 (markdown, on stdout)."""
import json
import os
import sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'sdk'))
import rld                      # noqa: E402
from rcc import driver          # noqa: E402

SDK = os.environ.get('C48SDK') or os.path.join(ROOT, '..', 'tuklusan', 'zx-ux-c48-sdk')
R = json.load(open(os.path.join(ROOT, 'sdk', 'tests', 'runs.json')))
rows = []
for n, r in R.items():
    if ':' in n:
        continue
    src = os.path.join(SDK, 'usr', 'src', r['dir'], r.get('src', n) + '.c')
    d1, g1, t1, o1, need1 = driver.build(src, {'heap': 1024})
    d2, g2, t2, o2, need2 = driver.build(src, {'heap': 1024, 'bytecode': 'all'})
    rows.append(dict(name=n, dir=r['dir'], src=os.path.getsize(src),
                     native_image=len(rld.parse_ssx(d1)['image']), native_need=need1,
                     bc_image=len(rld.parse_ssx(d2)['image']), bc_need=need2,
                     mode='bytecode' if need1 > driver.RUNIX_MAX else 'native'))
json.dump(rows, open(os.path.join(ROOT, 'build', 'sizes.json'), 'w'), indent=1)
order = ['games', 'apps', 'demos', 'examples', 'sound', 'security']
for x in sorted(rows, key=lambda x: (order.index(x['dir']), x['name'])):
    print('| `%s` | %s | %s | %s | %s | %s | %s | %s |' % (
        x['name'], x['dir'], format(x['src'], ','), format(x['native_image'], ','),
        format(x['native_need'], ','), format(x['bc_image'], ','), format(x['bc_need'], ','),
        '**bytecode**' if x['mode'] == 'bytecode' else 'native'))
