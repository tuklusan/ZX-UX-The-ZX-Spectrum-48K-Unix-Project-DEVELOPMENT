import re,subprocess,os,sys,collections
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
subprocess.run(['../tools/bin/sjasmplus','--nologo','--msg=war','--lst=unix.lst','unix.asm'],check=True,capture_output=True)
ins=[]   # (addr, bytes, text)
labels=set()
for l in open('unix.lst',errors='replace'):
    m=re.match(r'\s*\d+\+*\s+([0-9A-F]{4})\s((?:[0-9A-F]{2} ?)+?)\s{2,}(.*)$',l.rstrip('\n'))
    if not m: 
        m2=re.match(r'\s*\d+\+*\s+([0-9A-F]{4})\s+([\w.]+):',l)
        if m2: labels.add(int(m2.group(1),16))
        continue
    a=int(m.group(1),16); b=bytes.fromhex(m.group(2).replace(' ','')); txt=m.group(3)
    code=txt.split(';')[0]
    if re.match(r'^[\w.]+:',code): labels.add(a); code=code.split(':',1)[1]
    code=code.strip()
    if not code or re.match(r'(db|dw|ds|incbin|align|defb|defw)\b',code,re.I): ins.append((a,None,code)); continue
    ins.append((a,b,code))
def norm(a,b):
    op=b[0]
    if op in (0x18,0x20,0x28,0x30,0x38,0x10) and len(b)==2:
        return bytes([op])+((a+2+(b[1]-256 if b[1]>127 else b[1]))&0xFFFF).to_bytes(2,'little')
    return b
seq=[(a,norm(a,b),c) if b else (a,None,c) for a,b,c in ins]
term=lambda b: b and (b[0] in (0xC3,0xC9,0xE9) or (b[0]==0x18) or b[:2]==b'\xdd\xe9')
ends=[i for i,(a,b,c) in enumerate(seq) if term(b) and a>=0x6006]
best=[]
for x in range(len(ends)):
    for y in range(x+1,len(ends)):
        i,j=ends[x],ends[y]
        if seq[i][1]!=seq[j][1]: continue
        k=0; size=0
        while i-k>=0 and j-k>=0 and seq[i-k][1] and seq[i-k][1]==seq[j-k][1] and i-k!=j and j-k!=i:
            size+=len(seq[i-k][1])
            # stop growing past a label inside (except at the start)
            if k>0 and (seq[i-k+1][0] in labels or seq[j-k+1][0] in labels): size-=len(seq[i-k][1]); break
            k+=1
        if size>=4: best.append((size,seq[i-k+1][0],seq[j-k+1][0],k, [seq[q][2] for q in range(i-k+1,i+1)]))
best.sort(reverse=True)
seen=set()
for s,a1,a2,k,txt in best:
    if a2 in seen: continue
    seen.add(a2)
    print('%3d B  %04X ~ %04X  %s'%(s,a1,a2,' / '.join(t for t in txt)))
