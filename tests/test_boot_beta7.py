#!/usr/bin/env python3
"""Static symbol-derived single-CODE beta-0.0.7 TAP checks (external test)."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
KBASE = 0x6000


def blocks(raw):
    pos = 0
    items = []
    while pos < len(raw):
        assert pos + 2 <= len(raw), 'truncated length'
        n = int.from_bytes(raw[pos:pos+2], 'little')
        pos += 2
        assert 2 <= n <= 65535 and pos+n <= len(raw), 'truncated block'
        block = raw[pos:pos+n]
        pos += n
        parity = 0
        for ch in block:
            parity ^= ch
        assert parity == 0, 'bad block XOR'
        items.append(block)
    return items


def verify(raw, symbols, low, kernel, fs, merged):
    t = blocks(raw)
    assert len(t) == 4, 'exactly two header/data pairs required'
    h0, b0, h1, b1 = t
    assert len(h0) == 19 and h0[:2] == b'\0\0' and h0[2:7] == b'ZX-UX', 'BASIC header'
    assert len(b0) >= 4 and b0[0] == 0xff, 'BASIC data'
    assert int.from_bytes(h0[12:14], 'little') == len(b0)-2, 'BASIC length'
    assert len(h1) == 19 and h1[:2] == b'\0\x03' and h1[2:7] == b'ZX-UX', 'CODE header'
    assert int.from_bytes(h1[12:14], 'little') == len(merged), 'CODE size'
    lo = symbols['LOWK']
    assert int.from_bytes(h1[14:16], 'little') == lo, 'CODE load address'
    assert b1[0] == 255 and b1[1:-1] == merged, 'loaded bytes'
    assert lo + len(merged) < symbols['WINDOW'], 'image overlaps window'
    assert merged == low + bytes(KBASE - lo - len(low)) + kernel + fs, 'linkage image reconstruction'
    assert symbols['ITAB'] == KBASE + len(kernel), 'filesystem immediately after resident text'
    assert symbols['kend'] - KBASE <= 8192, 'kernel exceeds 8KiB'
    assert kernel[0] == 0xc3, 'kernel entry must jump to boot'
    assert merged[KBASE-lo] == 0xc3, '6000h entry replaced'
    assert b0[-2] == 0x0d, 'BASIC must end in ENTER'
    basic = b0[1:-1]
    marker = re.search(rb'\xfd\xb0"([0-9]+)"', basic)
    assert marker, 'no CLEAR VAL instruction'
    clear = int(marker.group(1))
    assert clear - (lo + len(merged)) >= 512, 'insufficient BASIC stack clearance'
    assert clear < 0xff00, 'unsafe BASIC RAMTOP'
    assert re.search(rb'\xef""\xaf', basic), 'missing single CODE LOAD'
    assert basic.count(b'\xef""\xaf') == 1, 'unexpected LOAD count'
    assert b'\xf9\xc0\xb0"24576"' in basic, 'missing 6000h entry'
    assert lo > 0x5ccb + len(basic) + 40, 'BASIC program workspace collides with image'
    return clear, lo + len(merged) - 1


def main():
    symbols = {}
    for line in (ROOT/'release/build/src/unix.sym').read_text().splitlines():
        m = re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)', line)
        if m:
            symbols[m.group(1)] = int(m.group(2), 16)
    args = [(ROOT/path).read_bytes() for path in (
        'release/build/out/ZX-UX.tap', 'release/build/out/lowk.bin',
        'release/build/out/unix.bin', 'release/build/out/fs.img',
        'release/build/out/merged-image.bin')]
    clear, end = verify(args[0], symbols, *args[1:])
    # Fail-closed checks on generated data, not stale historical snapshots.
    for label, blob in [('tampered CODE byte', lambda b: b.__setitem__(-31, b[-31] ^ 1)),
                        ('truncated tape', lambda b: b.__delitem__(slice(-4,None)))]:
        broken = bytearray(args[0])
        blob(broken)
        try:
            verify(bytes(broken), symbols, *args[1:])
        except AssertionError:
            pass
        else:
            raise AssertionError('negative tape sample accepted: ' + label)
    print('PASS: exact two-pair BASIC/CODE tape; checked loader/workspace/entry/gap')
    print('PASS: byte-exact merged linked image, parity and mutation rejection')
    print('BASIC CLEAR %04Xh; merged data ends %04Xh; stack margin %d' %
          (clear, end, clear-end))
    return 0


if __name__ == '__main__':
    sys.exit(main())
