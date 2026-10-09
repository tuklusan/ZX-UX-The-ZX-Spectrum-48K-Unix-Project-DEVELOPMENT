import re, glob, subprocess, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
JP = re.compile(r'^(\s*(?:[\w.]+:)?\s*)jp(\s+)((?:nz|z|nc|c)\s*,\s*)?([^(\s;][^;]*?)(\s*)(;.*)?$', re.I)
total = 0
for rnd in range(10):
    files = sorted(glob.glob('*.asm'))
    tags = {}
    n = 0
    for f in files:
        L = open(f).read().split('\n')
        for i, l in enumerate(L):
            if JP.match(l):
                L[i] = l + ' ;@J%d' % n
                tags[n] = (f, i)
                n += 1
        open(f, 'w').write('\n'.join(L))
    r = subprocess.run(['../tools/bin/sjasmplus', '--nologo', '--msg=war', '--lst=unix.lst', 'unix.asm'],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    conv = []
    for l in open('unix.lst', errors='replace'):
        m = re.search(r';@J(\d+)\s*$', l)
        if not m: continue
        mm = re.match(r'\s*\d+\+*\s+([0-9A-F]{4})\s+([0-9A-F]{2}) ([0-9A-F]{2}) ([0-9A-F]{2})', l)
        if not mm: continue
        addr = int(mm.group(1), 16); op = int(mm.group(2), 16)
        tgt = int(mm.group(4) + mm.group(3), 16)
        if op not in (0xC3, 0xC2, 0xCA, 0xD2, 0xDA) or addr < 0x6006: continue
        d = tgt - (addr + 2)
        if -128 <= d <= 127:
            conv.append(int(m.group(1)))
    # remove tags, convert
    for f in files:
        L = open(f).read().split('\n')
        for i, l in enumerate(L):
            m = re.search(r' ;@J(\d+)$', l)
            if m:
                l = l[:m.start()]
                if int(m.group(1)) in conv:
                    l = re.sub(r'\bjp\b', 'jr', l, count=1, flags=re.I)
                L[i] = l
        open(f, 'w').write('\n'.join(L))
    print('round', rnd, 'converted', len(conv))
    total += len(conv)
    if not conv: break
print('total', total)
