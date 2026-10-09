# tools/dev/ops.py - kept from the 2.2 size work; run from the repository root
import sys, collections; sys.path.insert(0,'sdk')
from rcc import driver
C='../tuklusan/zx-ux-c48-sdk/usr/src/demos/'
for n in sys.argv[1:]:
    st={}
    driver.compile_to_asm(C+n+'.c',{'bytecode':'all','stats':st})
    ops=collections.Counter(); bi=collections.Counter(); tri=collections.Counter()
    for fn in st['ops']:
        seq=[]; cur=None
        for it in fn:
            if it[0]=='o':
                if cur: seq.append(tuple(cur))
                cur=[it[1]]
            else:
                cur.append(it[1:] if it[0]!='a' else ('A',it[1]))
        if cur: seq.append(tuple(cur))
        names=[x[0] for x in seq]
        for x in seq: ops[x[0]]+=1
        for a,b in zip(names,names[1:]): bi[(a,b)]+=1
        for a,b,c in zip(names,names[1:],names[2:]): tri[(a,b,c)]+=1
    print(n, sum(ops.values()),'ops')
    print(ops.most_common(40)); print(bi.most_common(25)); print(tri.most_common(15))
