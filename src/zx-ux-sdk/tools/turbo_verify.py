"""Independent fail-closed compact boot-only TZX verifier.

This module deliberately does not call the turbo segment writer/parser. It
reads raw TZX bytes, checks both independent ROM bootstrap pairs and all 24
CRC-protected image segments, and bans noncompact waveform/audio blocks.
"""
from __future__ import annotations
import binascii
from pathlib import Path
import struct

COUNT = 24
MAX_BYTES = 30_000


def ensure(ok, message):
    if not ok:
        raise ValueError('Turbo TZX verification: ' + message)


def check_tzx(path: Path, image: bytes, bootstrap: bytes, *, load_base: int):
    tape = path.read_bytes()
    ensure(10 < len(tape) < MAX_BYTES, 'must be smaller than 30,000 bytes')
    ensure(tape[:10] == b'ZXTape!\x1a\x01\x14', 'TZX file signature/version')
    pos, records = 10, []
    while pos < len(tape):
        kind = tape[pos]
        if kind == 0x10:
            ensure(pos+5 <= len(tape), 'truncated ROM timing')
            pause, size = struct.unpack_from('<HH', tape, pos+1)
            head = pos+5
            end = head+size
            ensure(2 <= size <= 0xffff and end <= len(tape), 'truncated ROM block')
            packet = tape[head:end]
            parity = 0
            for byte in packet:
                parity ^= byte
            ensure(parity == 0, 'ROM block parity')
            records.append((kind, pause, packet))
        elif kind == 0x11:
            ensure(pos+19 <= len(tape), 'truncated turbo timing')
            timing = struct.unpack_from('<6H', tape, pos+1)
            ensure(timing == (2042, 875, 613, 513, 1025, 247), 'unapproved pulse timing')
            ensure(tape[pos+13] == 8, 'non-byte-aligned turbo segment')
            pause = struct.unpack_from('<H', tape, pos+14)[0]
            size = int.from_bytes(tape[pos+16:pos+19], 'little')
            head, end = pos+19, pos+19+size
            ensure(11 <= size <= 1200 and end <= len(tape), 'bad turbo size')
            records.append((kind, pause, tape[head:end]))
        else:
            raise ValueError('TZX cannot contain waveform/audio/unknown block %02x' % kind)
        pos = end
    ensure(pos == len(tape), 'trailing data')
    ensure(len(records) == 28, 'expected four ROM blocks and 24 turbo blocks')
    ensure([r[0] for r in records] == [0x10]*4+[0x11]*24, 'record order')
    for kind, (_, pause, block) in enumerate(records[:4]):
        ensure(pause == (1000,1000,1000,1500)[kind], 'ROM pause mismatch')
        ensure(block[0] == (0 if kind in (0,2) else 0xff), 'ROM flag mismatch')
    bashead, basic, codehead, code = (p[2] for p in records[:4])
    ensure(bashead[1] == 0 and codehead[1] == 3, 'header type mismatch')
    ensure(int.from_bytes(codehead[14:16],'little') == 0xD000, 'bootstrap must load at D000')
    ensure(int.from_bytes(codehead[12:14],'little') == len(bootstrap), 'bootstrap header length')
    ensure(code[1:-1] == bootstrap, 'bootstrap CODE bytes mismatch')
    ensure(b'52991' in basic and b'53248' in basic, 'unsafe BASIC loader')
    ensure(load_base < 0x6000 < load_base+len(image) <= 0xCE00, 'unsafe merged memory image')
    q,r = divmod(len(image), COUNT)
    ensure(q > 0, 'image too short')
    position = 0
    for ordinal, (_, pause, packet) in enumerate(records[4:], 1):
        n = q+(ordinal<=r)
        ensure(pause in (0,400), 'unreviewed turbo pause')
        ensure(len(packet) == n+11, 'segment length mismatch')
        ensure(packet[:4] == b'ZX\x01'+bytes((ordinal,)), 'segment magic/version/ordinal')
        ensure(struct.unpack_from('<HH',packet,4) == (position,n), 'segment destination/size')
        xor = 0
        for byte in packet:
            xor ^= byte
        ensure(xor == 0, 'segment XOR parity')
        expected_crc = binascii.crc_hqx(packet[:-3], 0xffff)
        ensure(packet[-3:-1] == struct.pack('<H', expected_crc), 'segment CRC16')
        ensure(packet[8:-3] == image[position:position+n], 'segment differs from canonical image')
        position += n
    ensure(position == len(image), 'incomplete reconstructed memory')
    return {'tzx_bytes': len(tape), 'boot_segments': COUNT,
            'image_bytes': len(image), 'bootstrap_bytes': len(bootstrap)}
