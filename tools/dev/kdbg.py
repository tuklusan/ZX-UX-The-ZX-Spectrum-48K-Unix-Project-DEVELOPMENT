import os
import sys, re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import zxrun
syms={}
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'unix.sym')):
    m=re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)',line)
    if m: syms[m.group(1)]=int(m.group(2),16)
rev=sorted((v,k) for k,v in syms.items() if 0x6000<=v<0xF000 and '.' not in k)
import bisect
def where(a):
    i=bisect.bisect_right([v for v,k in rev],a)-1
    return '%s+%d'%(rev[i][1],a-rev[i][0]) if i>=0 else hex(a)
zx=zxrun.ZX(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'test.z80'))
def w(a): return zx.mem[a]|zx.mem[a+1]<<8
def dump():
    KV=0x5B00
    r=zx.sim.registers
    print('PC=%04X %s SP=%04X'%(r[24],where(r[24]),r[12]))
    print('stat',[zx.mem[KV+i] for i in range(4)],'pid',[w(KV+12+2*i) for i in range(4)],'cur',zx.mem[KV+250],'wown',zx.mem[KV+98])
    print('save',['%04X'%w(KV+60+2*i) for i in range(4)],'img',['%04X'%w(KV+68+2*i) for i in range(4)],'brk',['%04X'%w(KV+36+2*i) for i in range(4)],'sp',['%04X'%w(KV+28+2*i) for i in range(4)])
    # arena
    a=syms['AR0']; out=[]
    while a < syms['AR1']:
        sz=w(a); k=zx.mem[a+2]
        out.append('%04X:%d/%d'%(a,sz,k))
        if sz==0: out.append('ZERO!'); break
        a+=sz
    print('arena',' '.join(out))
def stack(n=12):
    sp=zx.sim.registers[12]
    print(' '.join('%04X(%s)'%(w(sp+2*i),where(w(sp+2*i))) for i in range(n)))
for arg in sys.argv[1:]:
    if arg.startswith('t:'): zx.type(arg[2:].encode().decode('unicode_escape'))
    elif arg=='s': print(zx.screen())
    elif arg=='d': dump()
    elif arg=='k': stack()
    elif arg.isdigit(): zx.run(int(arg))
def arena_ok():
    a=syms['AR0']
    while a < syms['AR1']:
        sz=w(a); k=zx.mem[a+2]
        if sz < 4 or sz & 1 or k > 5: return False
        a+=sz
    return a == syms['AR1']
if 'watch' in sys.argv:
    script = list(b'root\n') + [None]*30 + list(b'ls -l /\n')
    f=0
    while f < 2000:
        if f > 300 and script:
            k=script.pop(0)
            if k is not None:
                zx.press(zxrun.keys_for(chr(k)))
        zx.run(1); f+=1
        if not arena_ok():
            print('arena broken at frame', f); dump(); stack(); break
def arena():
    a=syms['AR0']; out=[]
    while a < syms['AR1']:
        sz=w(a); k=zx.mem[a+2]
        out.append('%04X:%d/%d'%(a,sz,k))
        if sz<4: break
        a+=sz
    return ' '.join(out)
if 'watch2' in sys.argv:
    zx.run(300)
    zx.type('root\n')
    prev=arena()
    for f in range(400):
        zx.run(1)
        cur=arena()
        if cur!=prev:
            print('frame',zx.frames, where(zx.sim.registers[24])); print('  ',cur)
            prev=cur
        if not arena_ok(): break
def itab():
    t=syms['ITAB']
    for i in range(24):
        a=t+32*i
        fl=w(a)
        if fl & 0x8000:
            print(' ino %d flags %04X nl %d size %d dskp %04X rsvd %d'%(41+i,fl,zx.mem[a+2],w(a+4),w(a+6),w(a+30)))
if 'itab' in sys.argv: itab()
def strat(a):
    s=''
    while zx.mem[a] and len(s)<40:
        s+=chr(zx.mem[a]); a+=1
    return s
NAMES={0:'rele',1:'exit',2:'fork',3:'read',4:'write',5:'open',6:'close',7:'wait',8:'creat',9:'link',10:'unlink',11:'exec',12:'chdir',14:'mkdir',17:'break',18:'stat',19:'seek',28:'fstat',31:'stty',32:'gtty',34:'sleep',37:'zxpack',38:'ticks',39:'screen',40:'ssxmem',41:'ssxrun'}
def systrace(frames):
    r=zx.sim.registers
    se=syms['sysent']; sx=syms['sysx']
    end=r[25]+frames*zxrun.FRAME
    while r[25] < end:
        t=r[25]
        zx.sim.trace(r[24], se, 0, min(t+zxrun.FRAME, end), 1, None,None,None,None,None)
        if r[24]==se:
            a=r[0]; hl=r[6]<<8|r[7]; de=r[4]<<8|r[5]; bc=r[2]<<8|r[3]
            extra = strat(hl) if a in (5,8,11,12,14,18,10,9) else ''
            print('cur%d sys %s hl=%04X de=%04X bc=%04X %s'%(zx.mem[0x5B00+250],NAMES.get(a,a),hl,de,bc,extra), end='')
            zx.sim.trace(r[24], sx, 0, r[25]+50*zxrun.FRAME, 1, None,None,None,None,None)
            print(' -> CF=%d A=%d HL=%04X'%(r[1]&1, r[0], r[6]<<8|r[7]))
            zx.sim.trace(r[24], -1, 1, 0, 1, None,None,None,None,None)
if 'st' in sys.argv:
    zx.run(300); zx.type('root\n'); zx.run(300)
    zx.type('echo hello world >/tmp/a')
    zx.tr.pressed={'ENTER'}
    systrace(4)
    zx.tr.pressed=set()
    systrace(100)
