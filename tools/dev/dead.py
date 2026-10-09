import re,glob,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
files=sorted(glob.glob('*.asm'))+sorted(glob.glob('*.inc'))
src={f:open(f).read() for f in files}
build=open('../tools/build.py').read()
defs=[]
for f,t in src.items():
    L=t.split('\n')
    for i,l in enumerate(L):
        m=re.match(r'^([A-Za-z_]\w*):',l) or re.match(r'^([A-Za-z_]\w*)\s+equ\b',l,re.I)
        if m: defs.append((m.group(1),f,i,L))
allcode='\n'.join(re.sub(r';.*','',t) for t in src.values())
for name,f,i,L in defs:
    if name.startswith(('t_','e_')): continue
    n=len(re.findall(r'(?<![\w.])'+re.escape(name)+r'(?![\w])',allcode))
    if n<=1 and name not in build:
        # previous code line
        j=i-1
        while j>=0 and (not L[j].split(';')[0].strip()): j-=1
        prev=L[j].split(';')[0].strip() if j>=0 else ''
        ft = not re.match(r'^([\w.]+:)?\s*(jp|jr|ret|reti)\b(?!\s+(n?z|n?c|p|m|pe|po)\s*,)(?!\s+(n?z|n?c)\s*$)',prev.split(':')[-1].strip() if ':' in prev and not prev.startswith('db') else prev, re.I)
        print('%-12s %-11s:%-5d %s   (prev: %s)'%(name,f,i+1,'reachable by fallthrough' if ft else 'DEAD',prev[:40]))
