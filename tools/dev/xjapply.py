"""Automated cross-jumping: replace duplicated instruction tails (ending in
jp/jr/ret/jp(hl)) by a jump to one copy.  Byte-exact comparison, relative
jumps compared by absolute target; tails never extend past a label."""
import re,subprocess,os,glob
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
FILES=sorted(glob.glob('*.asm'))
TAG=re.compile(r' ;@L(\d+)$')
syms=None
def assemble():
    r=subprocess.run(['../tools/bin/sjasmplus','--nologo','--msg=war','--lst=unix.lst','--sym=unix.sym','unix.asm'],capture_output=True,text=True)
    assert r.returncode==0, r.stdout+r.stderr
def run_round(rnd):
    lines={}; n=0
    for f in FILES:
        L=open(f).read().split('\n')
        inmac=False
        for i,l in enumerate(L):
            code=l.split(';')[0]
            if re.match(r'^\s*MACRO\b',code): inmac=True
            if re.match(r'^\s*ENDM\b',code): inmac=False; continue
            if inmac: continue
            if code.strip() and not re.match(r'^\s*(MACRO|ENDM|include|org|DEVICE|ALIGN|SAVEBIN|ASSERT|if|endif)\b',code.strip().split(':')[-1].strip() if ':' in code else code.strip(),re.I) and 'equ' not in code.lower().split():
                L[i]=l+' ;@L%d'%n; lines[n]=(f,i); n+=1
        open(f,'w').write('\n'.join(L))
    assemble()
    kend=int(re.search(r'^kend: EQU 0x([0-9A-F]+)',open('unix.sym').read(),re.M).group(1),16)
    seq=[]; labels=set()
    for l in open('unix.lst',errors='replace'):
        t=TAG.search(l.rstrip('\n'))
        m=re.match(r'\s*\d+\+*\s+([0-9A-F]{4})\s((?:[0-9A-F]{2} ?)+?)\s{2,}(.*)$',l.rstrip('\n'))
        if t and not m:
            m2=re.match(r'\s*\d+\+*\s+([0-9A-F]{4})\s',l)
            if m2: labels.add(int(m2.group(1),16))
            seq.append((int(m2.group(1),16) if m2 else -1,None,None,int(t.group(1)))); continue
        if not (t and m): continue
        a=int(m.group(1),16); b=bytes.fromhex(m.group(2).replace(' ','')); code=m.group(3).split(';')[0]
        if re.match(r'^\s*[\w.]+:',code): labels.add(a); code=code.split(':',1)[1]
        code=code.strip().lower()
        if re.match(r'(db|dw|ds|defb|defw|incbin)\b',code): seq.append((a,None,None,int(t.group(1)))); continue
        op=b[0]
        nb=b
        if op in (0x18,0x20,0x28,0x30,0x38,0x10) and len(b)==2:
            nb=bytes([op])+((a+2+(b[1]-256 if b[1]>127 else b[1]))&0xFFFF).to_bytes(2,'little')
        if code.startswith('djnz'): nb=None   # loops: leave alone
        seq.append((a,nb,len(b),int(t.group(1))))
    term=lambda b: b and (b[0] in (0xC3,0xC9,0xE9,0x18))
    ends=[i for i,s in enumerate(seq) if term(s[1]) and s[0]>=0x6006]
    cands=[]
    for x in range(len(ends)):
        for y in range(len(ends)):
            if x==y: continue
            i,j=ends[x],ends[y]          # j: copy to replace, i: copy kept
            if seq[i][1]!=seq[j][1]: continue
            if (seq[i][0]<kend)!=(seq[j][0]<kend): continue
            k=0; size=0
            while i-k>=0 and j-k>=0 and seq[i-k][1] is not None and seq[i-k][1]==seq[j-k][1] and i-k!=j and j-k!=i:
                if k>0 and (seq[i-k+1][0] in labels or seq[j-k+1][0] in labels): break
                size+=seq[j-k][2]; k+=1
            # the replaced copy must not overlap the kept one
            if size>=4: cands.append((size-3,i-k+1,j-k+1,k))
    cands.sort(reverse=True)
    used=set(); plan=[]
    for gain,ia,jb,k in cands:
        ra=set(range(ia,ia+k)); rb=set(range(jb,jb+k))
        if ra&used or rb&used or ra&rb: continue
        used|=ra|rb; plan.append((gain,ia,jb,k))
    # apply: label before kept copy start, replace other copy by jp
    text={f:open(f).read().split('\n') for f in FILES}
    edits=[]
    for q,(gain,ia,jb,k) in enumerate(plan):
        fa,la=lines[seq[ia][3]]; loc='.xj%d_%d'%(rnd,q)
        L=text[fa]; g=la-1
        while not re.match(r'^[A-Za-z_]\w*:',L[g]) or re.match(r'^[A-Za-z_]\w*\s+equ\b',L[g],re.I): g-=1
        lab=re.match(r'^([A-Za-z_]\w*):',L[g]).group(1)+loc
        edits.append((fa,la,'ins',loc))
        for r in range(k):
            fb,lb=lines[seq[jb+r][3]]
            edits.append((fb,lb,'jp' if r==0 else 'del',lab))
    # apply per file bottom-up
    for f in FILES:
        L=text[f]
        for (ff,ln,kind,lab) in sorted([e for e in edits if e[0]==f],key=lambda e:(e[1],e[2]!='ins'),reverse=True):
            l=L[ln]
            if kind=='ins':
                L.insert(ln,lab+':')
            else:
                m=re.match(r'^([\w.]+:)?',l); lead=m.group(1) or ''
                if kind=='jp': L[ln]=(lead+' '*(8-len(lead)) if lead else '        ')+'jp '+lab+'  ; (shared tail)'
                else:
                    if lead: L[ln]=lead   # keep a label (never inside: checked)
                    else: L[ln]=None
        L=[re.sub(TAG,'',x) for x in L if x is not None]
        open(f,'w').write('\n'.join(L))
    return sum(p[0] for p in plan),len(plan)
tot=0
for rnd in range(6):
    g,n=run_round(rnd)
    print('round',rnd,'merged',n,'tails, ~%d bytes'%g); tot+=g
    if not n: break
assemble(); print('total ~',tot)
