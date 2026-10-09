# tools/dev/rstk.py - kept from the 2.2 size work; run from the repository root
# ZX-UX stack slack: hanoi and queens8 (STACK from argv) loaded together, full run
import sys
sys.path.insert(0,'tools'); sys.path.insert(0,'sdk'); sys.path.insert(0,'tests')
import zxrun, rtap, suite, rld
from rcc import driver
import os; S=os.path.join('build','dev')+os.sep; os.makedirs(S, exist_ok=True)
C='../tuklusan/zx-ux-c48-sdk/usr/src/demos/'
stack=sys.argv[1]
ssx={}
for n in ('hanoi','queens8'):
    o=S+n+'-s.ssx'; driver.main([C+n+'.c','-o',o,'--bytecode','--stack',stack]); ssx[n]=open(o,'rb').read()
s=suite.Session('build/test.z80'); s.login()
m=s.zx.mem; SC=suite.ksym('scrown'); PIMG=suite.ksym('p_img')
regions=[]
def find(n):
    h=rld.parse_ssx(ssx[n])
    for slot in range(4):
        b=m[PIMG+2*slot]|m[PIMG+2*slot+1]<<8
        if not b: continue
        for k in range(0,8):
            org=b+k
            img=rld.relocate(h['image'],h['relocs'],org)
            if bytes(m[org:org+64])==bytes(img[:64]):
                brk=org+len(img)+h['bss']+h['heap']
                return brk
    return None
for n,cnt in (('hanoi',1),('queens8',2)):
    s.zx.type('/dev/cassette/%s &\n'%n)
    s.zx.tr.edges=zxrun.tape_pulses(rtap.records(ssx[n],n), s.zx.sim.registers[25]+350000)
    k=0
    while bin(m[SC]).count('1')<cnt and k<5000: s.zx.run(10); k+=10
    brk=find(n)
    cur=m[suite.ksym('cur')]; PSP=suite.ksym('p_sp')
    sps=[s.zx.sim.registers[12]]+[m[PSP+2*i]|m[PSP+2*i+1]<<8 for i in range(4)]
    sp=min(x for x in sps if brk < x < brk+int(stack)+64)
    print(n,'brk %04X sp %04X'%(brk,sp))
    for a in range(brk, sp-24): m[a]=0xA5
    regions.append((n,brk))
    s.zx.run(50)
k=0
while m[SC] and k<80000: s.zx.run(500); k+=500
for n,brk in regions:
    a=brk
    while m[a]==0xA5: a+=1
    print(n,'stack',stack,'untouched',a-brk,'-> used',int(stack)-(a-brk))
print(s.screen())
