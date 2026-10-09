#!/usr/bin/env python3
"""rtap - runix SDK tape writer: SSX1 programs -> SST1 cassette records.

  rtap.py [-o out.tzx|out.tap] [--after runix.tzx] [--title T] prog.ssx[=NAME] ...

Each program becomes one standard Spectrum CODE pair (header + data block)
that runix's loader recognises (SPEC-SDK-R2 section 9):

  header   type 3, name = the program name (1..10 characters, the name
           typed as /dev/cassette/NAME), length = SSX1 file size,
           parameter 1 = bytes of memory the program needs (image, bss,
           heap and stack; at least the file size), parameter 2 = 'SS'
  data     the SSX1 file, flag FFh

--after appends the records to a copy of an existing tape (e.g. the runix
boot tape), so that one tape boots runix and then holds the programs.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rld  # noqa: E402

ARGS_ROOM = 0       # the loader adds the argument bytes itself


def tap_block(flag, data):
    body = bytes([flag]) + data
    x = 0
    for c in body:
        x ^= c
    return body + bytes([x])


def need(ssx):
    h = rld.parse_ssx(ssx)
    n = len(h['image']) + h['bss'] + h['heap'] + h['stack']
    return max(n, len(ssx))


def records(ssx, name):
    if not 1 <= len(name) <= 10 or not all(32 < ord(c) < 127 and c != '/' for c in name):
        raise SystemExit('rtap: bad program name %r' % name)
    n = need(ssx)
    if n > 0xFFFF:
        raise SystemExit('rtap: %s needs %d bytes' % (name, n))
    hdr = tap_block(0, bytes([3]) + name.encode().ljust(10) +
                    struct.pack('<HHH', len(ssx), n, 0x5353))
    return [hdr, tap_block(0xFF, ssx)]


def tzx_blocks(data):
    """-> list of (pause, block) from a TZX (standard speed blocks only)."""
    if data[:8] != b'ZXTape!\x1a':
        raise SystemExit('rtap: not a TZX file')
    p = 10
    out = []
    head = bytearray(data[:10])
    while p < len(data):
        t = data[p]
        if t == 0x10:
            pause, n = struct.unpack_from('<HH', data, p + 1)
            out.append((pause, data[p + 5:p + 5 + n]))
            p += 5 + n
        elif t == 0x30:
            n = data[p + 1]
            head += data[p:p + 2 + n]
            p += 2 + n
        elif t == 0x32:
            n = struct.unpack_from('<H', data, p + 1)[0]
            head += data[p:p + 3 + n]
            p += 3 + n
        else:
            raise SystemExit('rtap: TZX block %02X not supported' % t)
    return bytes(head), out


def write(out, head, blocks):
    if out.lower().endswith('.tap'):
        open(out, 'wb').write(b''.join(struct.pack('<H', len(b)) + b for _, b in blocks))
    else:
        body = bytearray(head)
        for pause, b in blocks:
            body += bytes([0x10]) + struct.pack('<HH', pause, len(b)) + b
        open(out, 'wb').write(bytes(body))


def main(argv):
    out, after, title = 'a.tzx', None, None
    progs = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('-o', '--after', '--title'):
            v = argv[i + 1]
            i += 2
            if a == '-o':
                out = v
            elif a == '--after':
                after = v
            else:
                title = v
            continue
        progs.append(a)
        i += 1
    if not progs:
        print(__doc__)
        return 2
    head = b'ZXTape!\x1a\x01\x14'
    blocks = []
    if after:
        head, blocks = tzx_blocks(open(after, 'rb').read())
    elif title:
        t = title.encode()
        head += bytes([0x30, len(t)]) + t
    for p in progs:
        path, _, name = p.partition('=')
        name = name or os.path.splitext(os.path.basename(path))[0][:10]
        ssx = open(path, 'rb').read()
        try:
            hdr, dat = records(ssx, name)
        except rld.LinkError as e:
            raise SystemExit('rtap: %s: %s' % (path, e))
        blocks += [(1000, hdr), (2000, dat)]
        print('%-10s %5d bytes, needs %5d' % (name, len(ssx), need(ssx)))
    write(out, head, blocks)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
