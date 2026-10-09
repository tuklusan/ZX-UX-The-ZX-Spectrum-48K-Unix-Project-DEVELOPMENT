# tools/dev/minstk.py - kept from the 2.2 size work; run from the repository root
import sys; sys.path.insert(0,'sdk')
import rvm
from rcc import driver
C='../tuklusan/zx-ux-c48-sdk/usr/src/demos/'
import os; S=os.path.join('build','dev')+os.sep; os.makedirs(S, exist_ok=True)
for n in ('hanoi','queens8'):
    lo,hi=200,600
    while lo<hi:
        mid=(lo+hi)//2
        o=S+n+'-m.ssx'; driver.main([C+n+'.c','-o',o,'--bytecode','--stack',str(mid)])
        v=rvm.VM(open(o,'rb').read()); why=v.run(200000)
        ok = why=='exit' and v.status==0
        if ok: hi=mid
        else: lo=mid+1
    print(n,'min stack',lo)
