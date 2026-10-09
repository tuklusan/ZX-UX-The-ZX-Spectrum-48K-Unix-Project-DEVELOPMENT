import os
import re,sys
syms={}
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'unix.sym')):
    m=re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)',line)
    if m and '.' not in m.group(1): syms[m.group(1)]=int(m.group(2),16)
items=sorted((v,k) for k,v in syms.items() if 0x6000<=v<syms['kend']+1)
sizes=[]
for (a,k),(b,_) in zip(items,items[1:]):
    sizes.append((b-a,k))
sizes.sort(reverse=True)
print('kernel', syms['kend']-0x6000, 'over', syms['kend']-0x6000-8192)
n=int(sys.argv[1]) if len(sys.argv)>1 else 40
print(' '.join('%s:%d'%(k,s) for s,k in sizes[:n]))
