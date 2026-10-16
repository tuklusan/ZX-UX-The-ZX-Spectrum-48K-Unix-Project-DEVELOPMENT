#!/usr/bin/env python3
"""External cassette wire-format checks. Source is never a build output."""
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'release/src/zx-ux-sdk'))
import rtap


def head(t, name, length, p1, p2):
    return rtap.tap_block(0, bytes((t,)) + name.encode().ljust(10, b' ') +
                          struct.pack('<HHH', length, p1, p2))


def member(n, version=5, name='demo'):
    payload = bytes((0,)) + struct.pack('<HHH', 0, n, n) + bytes(4) + b'/tmp/x\0' + bytes(range(251)) * (n // 251) + bytes(range(n % 251))
    blocks = [head(version, 'archive', 0, 0x8041, 0x5552),
              head(version, name, len(payload), 0x8046, 0x5552)]
    width = 1024 if version == 5 else 512
    for off in range(0, len(payload), width):
        chunk = payload[off:off + width]
        if len(chunk) == 17:
            chunk += b'\0'
        blocks.append(rtap.tap_block(255, chunk))
    blocks.append(head(version, '', 0, 0x8045, 0x5552))
    return blocks


def check(cond, why):
    if not cond:
        raise AssertionError(why)


def main():
    n = 0
    hello = (ROOT / 'release/dist/assets/c48-bin/ssx/hello.ssx').read_bytes()
    ss = rtap.records(hello, 'hello')
    check(ss[0][1] == 4 and ss[0][16:18] == b'SS', 'new SSX type/signature')
    check(any('program  /dev/cassette/hello' in x for x in rtap.list_blocks(ss)), 'new SSX listing')
    old = head(3, 'hello', len(hello), rtap.need(hello), 0x5353)
    check(any('program  /dev/cassette/hello' in x for x in rtap.list_blocks([old, ss[1]])), 'old SSX listing')
    for variant in (3, 5):
        for size in (0, 1, 17, 18, 511, 512, 513, 1023, 1024, 1025):
            tape = member(size, variant)
            lines = rtap.list_blocks(tape)
            check(len(lines) == 3 and '/tmp/x' in lines[1] and
                  not any('?' in x for x in lines), 'TAR roundtrip %d %d: %s' % (variant, size, lines))
            n += 1
            # Same data, flipped parity: should always be rejected.
            bad = tape[:]
            b = bytearray(bad[2]); b[-1] ^= 1; bad[2] = bytes(b)
            check('parity' in '\n'.join(rtap.list_blocks(bad)), 'TAR parity rejected')
            n += 1
            mixed = tape[:]
            mixed[1] = head(3 if variant == 5 else 5, 'demo',
                            len(tape[2]) - 2, 0x8046, 0x5552)
            check('invalid sequence, version' in '\n'.join(rtap.list_blocks(mixed)), 'mixed versions rejected')
            n += 1
    # An A header consumes no F data, and E consumes no following executable.
    lines = rtap.list_blocks([head(5,'a',0,0x8041,0x5552),
                              head(5,'',0,0x8045,0x5552)] + ss)
    check('end of archive' in lines[1] and 'program' in lines[2], 'A/E ordering')
    check('invalid archive end' in '\n'.join(rtap.list_blocks([head(5,'',0,0x8045,0x5552)])), 'orphan E')
    check('invalid sequence' in '\n'.join(rtap.list_blocks([head(5,'m',20,0x8046,0x5552)])), 'orphan F')
    check('archive missing end marker' in '\n'.join(rtap.list_blocks([head(5,'a',0,0x8041,0x5552)])), 'missing E')
    # Exactly 17 content bytes travel in an 18-byte physical block. Invalid
    # padding must be caught even with perfectly valid XOR parity.
    short = head(5, 'm', 17, 0x8046, 0x5552)
    wrong = rtap.tap_block(255, bytes(17) + b'!')
    lines = rtap.list_blocks([head(5,'a',0,0x8041,0x5552), short, wrong, head(5,'',0,0x8045,0x5552)])
    check('invalid 17-byte padding' in '\n'.join(lines), '17-byte padding')
    check('bad' in rtap.list_blocks([ss[0], rtap.tap_block(255, b'not-SSX')])[0], 'corrupt SSX data')
    print('PASS %d cassette archive/version/parity cases and host regression checks' % n)

if __name__ == '__main__':
    main()
