"""Cross-check ras encodings against sjasmplus for the whole instruction set."""
import os, subprocess, sys, tempfile, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import ras

R = ['a', 'b', 'c', 'd', 'e', 'h', 'l']
def lines():
    L = []
    for a in R + ['(hl)']:
        for b in R + ['(hl)']:
            if not (a == b == '(hl)'):
                L.append('ld %s,%s' % (a, b))
        L.append('ld %s,12h' % a)
    for x in ('ix', 'iy'):
        for r in R:
            L += ['ld %s,(%s+5)' % (r, x), 'ld (%s-3),%s' % (x, r)]
        L += ['ld (%s+1),99' % x, 'ld %s,1234h' % x, 'ld %s,(1234h)' % x, 'ld (1234h),%s' % x,
              'push %s' % x, 'pop %s' % x, 'ex (sp),%s' % x, 'jp (%s)' % x, 'ld sp,%s' % x,
              'inc %s' % x, 'dec %s' % x, 'inc (%s+2)' % x, 'dec (%s+2)' % x,
              'add %s,bc' % x, 'add %s,de' % x, 'add %s,%s' % (x, x), 'add %s,sp' % x]
        for op in ('add a,', 'adc a,', 'sub ', 'sbc a,', 'and ', 'xor ', 'or ', 'cp '):
            L.append('%s(%s+7)' % (op, x))
        for op in ('rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'srl'):
            L.append('%s (%s+4)' % (op, x))
        for b in range(8):
            L += ['bit %d,(%s+1)' % (b, x), 'set %d,(%s-1)' % (b, x), 'res %d,(%s)' % (b, x)]
    L += ['ld a,(bc)', 'ld a,(de)', 'ld (bc),a', 'ld (de),a', 'ld a,(4000h)', 'ld (4000h),a',
          'ld a,i', 'ld a,r', 'ld i,a', 'ld r,a', 'ld sp,hl', 'ex de,hl', "ex af,af'", 'ex (sp),hl',
          'jp (hl)']
    for rp in ('bc', 'de', 'hl', 'sp'):
        L += ['ld %s,1234h' % rp, 'ld %s,(5678h)' % rp, 'ld (5678h),%s' % rp,
              'inc %s' % rp, 'dec %s' % rp, 'add hl,%s' % rp, 'adc hl,%s' % rp, 'sbc hl,%s' % rp]
    for rp in ('bc', 'de', 'hl', 'af'):
        L += ['push %s' % rp, 'pop %s' % rp]
    for op in ('add a,', 'adc a,', 'sub ', 'sbc a,', 'and ', 'xor ', 'or ', 'cp '):
        for r in R + ['(hl)']:
            L.append(op + r)
        L.append(op + '55h')
    for r in R + ['(hl)']:
        L += ['inc %s' % r, 'dec %s' % r]
        for op in ('rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'srl'):
            L.append('%s %s' % (op, r))
        for b in range(8):
            L += ['bit %d,%s' % (b, r), 'set %d,%s' % (b, r), 'res %d,%s' % (b, r)]
        if r != '(hl)':
            L += ['in %s,(c)' % r, 'out (c),%s' % r]
    for cc in ('nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm'):
        L += ['jp %s,1234h' % cc, 'call %s,1234h' % cc, 'ret %s' % cc]
    for cc in ('nz', 'z', 'nc', 'c'):
        L.append('jr %s,$+10' % cc)
    L += ['jr $', 'djnz $-5', 'jp 1234h', 'call 1234h', 'ret', 'in a,(0feh)', 'out (0feh),a',
          'im 0', 'im 1', 'im 2'] + ['rst %d' % (k * 8) for k in range(8)]
    L += list(ras.SIMPLE)
    return L

def main():
    L = lines()
    src = '\n'.join(' ' + l for l in L) + '\n'
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, 'a.asm'), 'w').write(' org 0\n' + src)
        sj = os.path.join(HERE, '..', '..', 'tools', 'bin', 'sjasmplus')
        r = subprocess.run([sj, '--nologo', '--raw=' + os.path.join(td, 'a.bin'), os.path.join(td, 'a.asm')],
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout, r.stderr)
            return 1
        ref = open(os.path.join(td, 'a.bin'), 'rb').read()
    # per line compare
    a = ras.Asm('t')
    a.load(src)
    a.assemble()
    got = bytes(a.out['text'])
    if got == ref:
        print('ras: %d instructions match sjasmplus (%d bytes)' % (len(L), len(got)))
        return 0
    pos = 0
    for l in L:
        b = ras.Asm('x'); b.load(' org 0\n' if False else ' ' + l); b.assemble()
        o = bytes(b.out['text'])
        if ref[pos:pos + len(o)] != o:
            print('MISMATCH', l, o.hex(), ref[pos:pos + len(o) + 2].hex())
            return 1
        pos += len(o)
    return 1

if __name__ == '__main__':
    sys.exit(main())
