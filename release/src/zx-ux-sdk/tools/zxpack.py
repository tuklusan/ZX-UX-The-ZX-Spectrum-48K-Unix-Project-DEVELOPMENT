#!/usr/bin/env python3
"""zxpack - reference codec for the ZX-UX UNIX v1 file compressor.

Bit-exact model of the kernel's Z80 implementation (src/zx.asm): the
build uses it to store files packed on the RAM disk image, and the test
harness uses it to cross-check streams packed by the Spectrum.

Format: LZ77 with a 2 KB window, every decision coded with an adaptive
binary range coder (16-bit size and low, renormalised one bit at a time
before each decision, carries added into the output; 8-bit probabilities
of a 0, adaptation shift 4).  The encoder ends with the 16 bits of low.  The stream has no header and no end
marker: the logical length is the file size kept in the i-node.

    token        coded as
    literal      m[st]=0, 8-bit tree (255 probabilities)
    match        m[st]=1, r[st]=0, gamma((off-1)/16+1) [off], 4-bit tree
                 of (off-1)%16 [olo], gamma(len-2) [len], len >= 3
    repeat match m[st]=1, r[st]=1, gamma(len-1) [len], last offset again

  st = the type of the previous token: 0 literal, 1 match, 2 repeat.  gamma(v) codes v >= 1 as
  adaptive Elias gamma: before each mantissa bit k a "more" bit with its
  own probability P[2k], the bit itself with P[2k+1]; the final "stop"
  bit uses P[2n].

  Parse (greedy with one step of lazy evaluation):
    rl  = length of the repeat match at p      (0 if no last offset)
    L   = longest match at p, nearest offset wins ties, L < 3 -> 0
    if L and p+1 < n and rl < L and longest(p+1) > L+1: L = rl = 0
    rl >= 2 and rl+1 >= L -> repeat match;  L -> match;  else literal
"""
import sys
from pathlib import Path

WIN = 2048
PB, SH = 8, 4
ONE = 1 << PB


class Enc:
    """Encoder: 16-bit low and size; the bits shifted out of low are
    final except for carries, which are added into the output."""
    def __init__(s):
        s.low, s.size = 0, 0xFFFF
        s.bits = []

    def bit(s, P, i, b):
        while s.size < 0x8000:
            s.size <<= 1
            s.low <<= 1
            s.bits.append(s.low >> 16)
            s.low &= 0xFFFF
        p = P[i]
        t = (s.size * p) >> PB
        if b:
            s.low += t
            if s.low > 0xFFFF:
                s.low &= 0xFFFF
                k = len(s.bits) - 1
                while s.bits[k]:
                    s.bits[k] = 0
                    k -= 1
                s.bits[k] = 1
            s.size -= t
            P[i] = p - (p >> SH)
        else:
            s.size = t
            P[i] = p + ((ONE - p) >> SH)
        return b

    def finish(s):
        for k in range(15, -1, -1):
            s.bits.append((s.low >> k) & 1)
        while len(s.bits) % 8:
            s.bits.append(0)
        return bytes(int(''.join(map(str, s.bits[k:k + 8])), 2)
                     for k in range(0, len(s.bits), 8))


class Dec:
    def __init__(s, d):
        s.d = d; s.p = 0; s.acc = 0; s.n = 0
        s.size = 0xFFFF; s.v = 0
        for _ in range(16):
            s.v = (s.v << 1) | s._ib()

    def _ib(s):
        if s.n == 0:
            s.acc = s.d[s.p] if s.p < len(s.d) else 0
            s.p += 1; s.n = 8
        s.n -= 1
        return (s.acc >> s.n) & 1

    def bit(s, P, i, b=None):
        while s.size < 0x8000:
            s.size <<= 1
            s.v = (s.v << 1) | s._ib()
        p = P[i]
        t = (s.size * p) >> PB
        if s.v >= t:
            b = 1; s.v -= t; s.size -= t; P[i] = p - (p >> SH)
        else:
            b = 0; s.size = t; P[i] = p + ((ONE - p) >> SH)
        return b


def model():
    h = ONE // 2
    return dict(m=[h] * 3, r=[h] * 3, lit=[h] * 256, len=[h] * 32,
                off=[h] * 32, olo=[h] * 16)


def gamma(c, P, v=None):
    if v is not None:
        n = v.bit_length() - 1
        for k in range(n):
            c.bit(P, 2 * k, 1)
            c.bit(P, 2 * k + 1, (v >> (n - 1 - k)) & 1)
        c.bit(P, 2 * n, 0)
        return v
    v = 1; k = 0
    while c.bit(P, 2 * k):
        v = (v << 1) | c.bit(P, 2 * k + 1); k += 1
    return v


def tree(c, P, nb, v=None):
    i = 1
    for k in range(nb - 1, -1, -1):
        if v is None:
            b = c.bit(P, i)
        else:
            b = c.bit(P, i, (v >> k) & 1)
        i = (i << 1) | b
    return i & ((1 << nb) - 1)


def longest(d, i):
    bl = bo = 0; n = len(d)
    for j in range(i - 1, max(0, i - WIN) - 1, -1):
        if d[j] != d[i]:
            continue
        L = 1
        while i + L < n and d[j + L] == d[i + L]:
            L += 1
        if L > bl:
            bl, bo = L, i - j
    return bl, bo


def replen(d, i, off):
    if off == 0 or off > i:
        return 0
    L = 0; n = len(d)
    while i + L < n and d[i + L - off] == d[i + L]:
        L += 1
    return L


def pack(d):
    e = Enc(); M = model(); st = 0; rep = 0; i = 0; n = len(d)
    while i < n:
        rl = replen(d, i, rep)
        L, off = longest(d, i)
        if L < 3:
            L = 0
        if L and i + 1 < n and rl < L and longest(d, i + 1)[0] > L + 1:
            L = rl = 0
        if rl >= 2 and rl + 1 >= L:
            e.bit(M['m'], st, 1); e.bit(M['r'], st, 1)
            gamma(e, M['len'], rl - 1); i += rl; st = 2
        elif L:
            e.bit(M['m'], st, 1); e.bit(M['r'], st, 0)
            gamma(e, M['off'], ((off - 1) >> 4) + 1)
            tree(e, M['olo'], 4, (off - 1) & 15)
            gamma(e, M['len'], L - 2); rep = off; i += L; st = 1
        else:
            e.bit(M['m'], st, 0); tree(e, M['lit'], 8, d[i]); i += 1; st = 0
    return e.finish()


def unpack(s, n):
    c = Dec(s); M = model(); st = 0; rep = 0; out = bytearray()
    while len(out) < n:
        if c.bit(M['m'], st):
            if c.bit(M['r'], st):
                L = gamma(c, M['len']) + 1; st = 2
            else:
                rep = ((gamma(c, M['off']) - 1) << 4) + tree(c, M['olo'], 4) + 1
                L = gamma(c, M['len']) + 2; st = 1
            for _ in range(L):
                out.append(out[-rep])
        else:
            out.append(tree(c, M['lit'], 8)); st = 0
    return bytes(out)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == '-d':
        d = Path(a[1]).read_bytes()
        n = int.from_bytes(d[:2], 'little')
        open(a[2], 'wb').write(unpack(d[2:], n))
    elif len(a) == 2:
        d = open(a[0], 'rb').read()
        p = pack(d)
        assert unpack(p, len(d)) == d
        Path(a[1]).write_bytes(len(d).to_bytes(2, 'little') + p)
        print(f"{len(d)} -> {len(p)} bytes ({100 * len(p) / max(1, len(d)):.1f}%)")
    else:
        sys.exit("usage: zxpack.py in out.zxp | zxpack.py -d in.zxp out")
