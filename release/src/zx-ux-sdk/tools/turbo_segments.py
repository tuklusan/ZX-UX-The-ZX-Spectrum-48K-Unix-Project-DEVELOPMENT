"""Boot-only ZX-UX beta-0.0.7 TZX segment framing (not userland tape I/O).

This module is intentionally a packet generator, not a substitute for a
reviewed Z80 bootstrap or a genuine speed/ROM/FUSE load test.  A caller must
provide separately checked bootstrap and BASIC blocks before a bootable TZX
can be considered. No historical commercial loader instructions are used.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct

COUNT = 24
# Strictly less than 30,000 decimal bytes, not a 30 KiB approximation.
MAX_TZX_BYTES = 30_000
LOAD_BASE = 0x5D98
ENTRY = 0x6000
MAGIC = b'ZX'
VERSION = 1
TIMINGS = (2042, 875, 613, 513, 1025, 247)


class TurboFormatError(ValueError):
    """A malformed, missing, or misordered boot segment."""


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xffff
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xffff
    return crc


def xor_bytes(data: bytes) -> int:
    value = 0
    for b in data:
        value ^= b
    return value


def layout(image_length: int, *, load_base: int = LOAD_BASE):
    if not 0 < image_length <= 0xffff:
        raise TurboFormatError('image length outside 16-bit transport')
    if not 0 <= load_base < ENTRY < load_base + image_length <= 0xce00:
        raise TurboFormatError('load and entry must fit below protected boot stack')
    q, r = divmod(image_length, COUNT)
    if not q:
        raise TurboFormatError('image too short for 24 nonempty segments')
    sizes = [q + (i < r) for i in range(COUNT)]
    offsets = []
    position = 0
    for size in sizes:
        offsets.append((position, size))
        position += size
    assert position == image_length
    return tuple(offsets)


def make_segments(image: bytes, *, load_base: int = LOAD_BASE):
    """Encode v1 ZX envelope, CRC16 and XOR; offsets are image-relative."""
    if not isinstance(image, bytes):
        raise TypeError('image must be bytes')
    packets = []
    for index, (offset, size) in enumerate(layout(len(image), load_base=load_base), start=1):
        envelope = MAGIC + bytes((VERSION, index)) + struct.pack('<HH', offset, size) + image[offset:offset+size]
        with_crc = envelope + struct.pack('<H', crc16_ccitt_false(envelope))
        packets.append(with_crc + bytes((xor_bytes(with_crc),)))
    return tuple(packets)


def pack_turbo_record(packet: bytes, *, pause_ms: int) -> bytes:
    if not 0 <= pause_ms <= 0xffff:
        raise TurboFormatError('turbo pause outside TZX unsigned 16-bit value')
    if not 11 <= len(packet) <= 0xffffff:
        raise TurboFormatError('invalid turbo record length')
    if not isinstance(packet, bytes):
        raise TypeError('packet must be bytes')
    pilot, sync1, sync2, zero, one, count = TIMINGS
    return (bytes([0x11]) + struct.pack('<HHHHHHBH', pilot, sync1, sync2,
                                       zero, one, count, 8, pause_ms)
            + len(packet).to_bytes(3, 'little') + packet)


def read_packet(packet: bytes, *, ordinal: int, offset: int, size: int) -> bytes:
    """Fail closed; no tape-supplied destination can override linked layout."""
    if len(packet) != size + 11:
        raise TurboFormatError('segment length mismatch')
    if packet[:2] != MAGIC or packet[2] != VERSION:
        raise TurboFormatError('segment magic/version mismatch')
    if packet[3] != ordinal:
        raise TurboFormatError('segment ordinal mismatch')
    if struct.unpack('<HH', packet[4:8]) != (offset, size):
        raise TurboFormatError('segment offset/length mismatch')
    if xor_bytes(packet) != 0:
        raise TurboFormatError('segment XOR mismatch')
    if struct.unpack('<H', packet[-3:-1])[0] != crc16_ccitt_false(packet[:-3]):
        raise TurboFormatError('segment CRC mismatch')
    return packet[8:-3]


def read_segments(packets, *, image_length: int, load_base: int = LOAD_BASE) -> bytes:
    plan = layout(image_length, load_base=load_base)
    if len(packets) != COUNT:
        raise TurboFormatError('expected exactly 24 segments')
    result = bytearray(image_length)
    for ordinal, ((offset, size), packet) in enumerate(zip(plan, packets), start=1):
        result[offset:offset+size] = read_packet(packet, ordinal=ordinal,
                                                  offset=offset, size=size)
    return bytes(result)


def pack_standard_tzx_block(block: bytes, pause_ms: int) -> bytes:
    if not 0 <= pause_ms <= 0xffff or not 2 <= len(block) <= 0xffff:
        raise TurboFormatError('invalid ROM-standard block')
    if xor_bytes(block):
        raise TurboFormatError('ROM-standard block parity failed')
    return b'\x10' + struct.pack('<HH', pause_ms, len(block)) + block


def pack_tzx(basic_pair, bootstrap_pair, image: bytes, *, pause_ms: int, load_base: int = LOAD_BASE) -> bytes:
    """Frame four ROM 10h records and 24 turbo 11h records.

    Strictly framing only: successful construction is NOT runtime validation
    of the separately provided ROM-standard BASIC/bootstrap code.
    """
    if len(basic_pair) != 2 or len(bootstrap_pair) != 2:
        raise TurboFormatError('two ROM header/data pairs are required')
    records = [pack_standard_tzx_block(block, gap) for block, gap in
               zip((*basic_pair, *bootstrap_pair), (1000, 1000, 1000, 1500))]
    records.extend(pack_turbo_record(p, pause_ms=pause_ms) for p in
                   make_segments(image, load_base=load_base))
    tape = b'ZXTape!\x1a\x01\x14' + b''.join(records)
    if len(tape) >= MAX_TZX_BYTES:
        raise TurboFormatError('compact boot TZX must be smaller than 30,000 bytes')
    return tape
