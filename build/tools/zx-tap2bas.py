#!/usr/bin/env python3
# ZX-UX — ZX Spectrum 48K TAP-to-BASIC LLIST converter
# Copyright (c) 2026 Supratim Sanyal of SANYALnet Labs.
# Based on original work by Supratim Sanyal of SANYALnet Labs.
# License: ZX-UX repository LICENSE (non-commercial terms and attribution).
#
# File: zx-tap2bas.py
# Purpose: Recover an ASCII Sinclair BASIC listing from a raw TAP tape.
# Scope: ROM's logical LLIST character stream before ZX Printer bitmap/layout.
# Dependencies: Python 3 standard library only; no other ZX-UX script, ROM or
#               emulator is required.
"""Generate ROM-LLIST-spaced Spectrum BASIC text from a raw TAP tape.

This is a standalone TAP reader and formatter.  It reproduces the logical
character stream emitted by the original Sinclair Spectrum 48K ROM's LLIST
path, before the printer bitmap engine, and serializes that stream as the same
reversible ASCII form used by the ZX-UX BASIC exporters.

Example:
    python3 build/tools/zx-tap2bas.py game.tap -o staged/game.bas
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


# These bytes were copied, without translation, from 0096h..0204h (inclusive)
# of the verified 16 KiB Sinclair 48K ROM.  The table contains the 91 token
# spellings A5h..FFh, with bit 7 set on each entry's final character.
ROM_TOKEN_TABLE = bytes.fromhex('''
    52 4e c4 49 4e 4b 45 59 a4 50 c9 46 ce 50 4f 49 4e d4 53 43 52 45 45 4e
    a4 41 54 54 d2 41 d4 54 41 c2 56 41 4c a4 43 4f 44 c5 56 41 cc 4c 45 ce
    53 49 ce 43 4f d3 54 41 ce 41 53 ce 41 43 d3 41 54 ce 4c ce 45 58 d0 49
    4e d4 53 51 d2 53 47 ce 41 42 d3 50 45 45 cb 49 ce 55 53 d2 53 54 52 a4
    43 48 52 a4 4e 4f d4 42 49 ce 4f d2 41 4e c4 3c bd 3e bd 3c be 4c 49 4e
    c5 54 48 45 ce 54 cf 53 54 45 d0 44 45 46 20 46 ce 43 41 d4 46 4f 52 4d
    41 d4 4d 4f 56 c5 45 52 41 53 c5 4f 50 45 4e 20 a3 43 4c 4f 53 45 20 a3
    4d 45 52 47 c5 56 45 52 49 46 d9 42 45 45 d0 43 49 52 43 4c c5 49 4e cb
    50 41 50 45 d2 46 4c 41 53 c8 42 52 49 47 48 d4 49 4e 56 45 52 53 c5 4f
    56 45 d2 4f 55 d4 4c 50 52 49 4e d4 4c 4c 49 53 d4 53 54 4f d0 52 45 41
    c4 44 41 54 c1 52 45 53 54 4f 52 c5 4e 45 d7 42 4f 52 44 45 d2 43 4f 4e
    54 49 4e 55 c5 44 49 cd 52 45 cd 46 4f d2 47 4f 20 54 cf 47 4f 20 53 55
    c2 49 4e 50 55 d4 4c 4f 41 c4 4c 49 53 d4 4c 45 d4 50 41 55 53 c5 4e 45
    58 d4 50 4f 4b c5 50 52 49 4e d4 50 4c 4f d4 52 55 ce 53 41 56 c5 52 41
    4e 44 4f 4d 49 5a c5 49 c6 43 4c d3 44 52 41 d7 43 4c 45 41 d2 52 45 54
    55 52 ce 43 4f 50 d9
''')
ROM_TOKEN_TABLE_SHA256 = '32874566b963014669040a63e04913db95d92b63d5dff513aefdcae2a0343f60'


class TapeError(ValueError):
    """The source tape is malformed, ambiguous, or unsupported."""


def _take(data: bytes, offset: int, size: int, what: str) -> tuple[bytes, int]:
    if size < 0 or offset + size > len(data):
        raise TapeError(f'{what}: truncated at offset {offset}')
    return data[offset:offset + size], offset + size


def _u16(data: bytes, at: int) -> int:
    return int.from_bytes(data[at:at + 2], 'little')


def tap_blocks(tape: bytes):
    """Walk a raw TAP stream, yielding complete flag+data+XOR blocks."""
    pos = 0
    number = 0
    while pos < len(tape):
        prefix_at = pos
        prefix, pos = _take(tape, pos, 2, f'TAP block {number} length')
        size = _u16(prefix, 0)
        if size < 2:
            raise TapeError(f'TAP block {number} at offset {prefix_at}: too short')
        payload, pos = _take(tape, pos, size, f'TAP block {number}')
        check = 0
        for byte in payload:
            check ^= byte
        if check:
            raise TapeError(f'TAP block {number} at offset {prefix_at}: XOR checksum mismatch')
        yield payload
        number += 1


def basic_programs(tape: bytes):
    """Pair Spectrum BASIC headers with their immediately following data."""
    pending = None
    for block in tap_blocks(tape):
        if block[0] == 0 and len(block) == 19:
            if pending:
                raise TapeError('new header before previous BASIC data')
            # Format: flag, type, ten-byte name, length, autostart, vars, XOR.
            if block[1] == 0:
                pending = (block[2:12], _u16(block, 12), _u16(block, 16))
            continue
        if pending is not None:
            name, expected, vars_offset = pending
            pending = None
            if block[0] != 0xff:
                raise TapeError('BASIC header not followed by a data block')
            program = block[1:-1]
            if len(program) != expected:
                raise TapeError(f'BASIC {name!r}: expected {expected} bytes, got {len(program)}')
            if vars_offset > len(program):
                raise TapeError(f'BASIC {name!r}: variables offset outside program')
            yield name, program[:vars_offset]
    if pending:
        raise TapeError('missing BASIC data block after header')


def numbered_lines(program: bytes):
    """Decode Spectrum BASIC line headers and validate every line boundary."""
    pos = 0
    last = -1
    while pos < len(program):
        header, pos = _take(program, pos, 4, 'BASIC line header')
        number = int.from_bytes(header[:2], 'big')
        size = _u16(header, 2)
        if not 0 <= number <= 9999 or number <= last:
            raise TapeError(f'BASIC line numbers out of order: {last}, {number}')
        if size == 0:
            raise TapeError(f'Line {number}: zero-length BASIC line')
        contents, pos = _take(program, pos, size, f'Line {number}')
        if contents[-1] != 13:
            raise TapeError(f'Line {number}: no end-of-line marker')
        cursor = 0
        while cursor < len(contents) - 1:
            value = contents[cursor]
            if value == 14:
                if cursor + 6 > len(contents) - 1:
                    raise TapeError(f'Line {number}: truncated numeric cache')
                cursor += 6
                continue
            if value == 13:
                raise TapeError(f'Line {number}: embedded ROM end-of-line at offset {cursor}')
            cursor += 1
        last = number
        yield number, contents[:-1]


def _rom_token_entries() -> tuple[tuple[bytes, int, int], ...]:
    """Read the embedded original ROM table and retain its raw end bytes."""
    if (len(ROM_TOKEN_TABLE) != 367
            or hashlib.sha256(ROM_TOKEN_TABLE).hexdigest() != ROM_TOKEN_TABLE_SHA256):
        raise TapeError('embedded original 48K ROM token table failed integrity check')
    pos = 0
    entries = []
    for token in range(0xA5, 0x100):
        start = pos
        while pos < len(ROM_TOKEN_TABLE) and not (ROM_TOKEN_TABLE[pos] & 128):
            pos += 1
        if pos >= len(ROM_TOKEN_TABLE) or pos - start > 40:
            raise TapeError(f'ROM keyword {token:02X} has no valid high-bit terminator')
        raw = ROM_TOKEN_TABLE[start:pos + 1]
        pos += 1
        word = bytes(c & 0x7f for c in raw)
        if not word or any(not 32 <= c < 127 for c in word):
            raise TapeError(f'ROM keyword {token:02X} contains invalid characters')
        entries.append((word, raw[0], raw[-1]))
    if entries[0][0] != b'RND' or entries[0xCB - 0xA5][0] != b'THEN' or entries[-1][0] != b'COPY':
        raise TapeError('unexpected 48K ROM keyword sequence')
    if pos != len(ROM_TOKEN_TABLE):
        raise TapeError('embedded ROM token table contains trailing bytes')
    return tuple(entries)


def llist_segments(number: int, body: bytes):
    """Port the ROM LLIST character-output path before printer pixels."""
    if not 0 <= number <= 9999:
        raise TapeError(f'invalid BASIC line number {number}')
    token_entries = _rom_token_entries()
    parts = [(f'{number:4d}'.encode('ascii'), None, False)]
    flags_0 = False

    def emit(byte: int) -> None:
        nonlocal flags_0
        if 32 <= byte < 128:
            flags_0 = (byte == 32)

    pos = 0
    while pos < len(body):
        value = body[pos]
        if value == 13:
            break
        if value == 14:
            if pos + 6 > len(body):
                raise TapeError(f'Line {number}: truncated five-byte numeric value at offset {pos}')
            pos += 6
            continue
        if value < 0xA5:
            emit(value)
            parts.append((bytes([value]), value, False))
        else:
            index = value - 0xA5
            word, first, last = token_entries[index]
            out = bytearray()
            if index >= 0x20 and first >= 0x41 and not flags_0:
                out.append(32)
                emit(32)
            for character in word:
                out.append(character)
                emit(character)
            last_doubled = (last << 1) & 255
            if index >= 3 and (last_doubled == 0x48 or last_doubled >= 0x82):
                out.append(32)
                emit(32)
            parts.append((bytes(out), value, True))
        pos += 1
    return parts


def list_line(number: int, body: bytes) -> str:
    """Serialize one LLIST line as ASCII with reversible byte escapes."""
    parts = llist_segments(number, body)
    quoted = rem = data = False
    rendered = []
    for segment, original, expanded in parts:
        if original is None:
            rendered.append(segment.decode('ascii'))
            continue
        if expanded:
            if quoted or rem or data:
                rendered.append(f'{{{original:02X}}}')
            else:
                rendered.append(segment.decode('ascii'))
            if not quoted and not rem and not data and original == 0xEA:
                rem = True
            if not quoted and not rem and original == 0xE4:
                data = True
        elif original == 34 and not rem:
            quoted = not quoted
            rendered.append('"')
        elif original == 58 and not quoted and not rem:
            data = False
            rendered.append(':')
        elif original == 96 or original in (123, 125) or original < 32 or original >= 127:
            rendered.append(f'{{{original:02X}}}')
        else:
            rendered.append(chr(original))
    if quoted:
        raise TapeError(f'Line {number}: unterminated quoted string')
    return ''.join(rendered)


def listing(tape: bytes, *, program_index: int | None = None) -> str:
    """Render one selected BASIC program from a TAP image."""
    _rom_token_entries()
    programs = list(basic_programs(tape))
    if not programs:
        raise TapeError('TAP contains no Spectrum BASIC program header/data pair')
    if program_index is None:
        if len(programs) != 1:
            raise TapeError(f'TAP contains {len(programs)} BASIC programs; specify --program-index')
        program_index = 0
    if not 0 <= program_index < len(programs):
        raise TapeError(f'program index {program_index} outside 0..{len(programs) - 1}')
    name, program = programs[program_index]
    result = [list_line(number, body) for number, body in numbered_lines(program)]
    if not result:
        raise TapeError(f'BASIC program {name!r} has no lines')
    return '\n'.join(result) + '\n'


def _protected_listing_destination(path: Path) -> bool:
    """Never generate into a preserved 60-game BASIC directory."""
    parts = path.resolve().parts
    for i in range(len(parts) - 3):
        if (parts[i:i + 2] == ('bonus', '60-programs')
                and parts[i + 2][:2].isdigit() and parts[i + 3] == 'BASIC'):
            return True
    return False


def _write_listing(path: Path, content: str, inputs: tuple[Path, ...]) -> None:
    """Atomically reserve a new output filename and never overwrite input."""
    destination = path.resolve()
    if destination in (item.resolve() for item in inputs) or _protected_listing_destination(destination):
        raise TapeError(f'protected destination: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='ascii', newline='\n') as output:
        output.write(content)


def main(argv=None):
    """Command-line entrance; the TAP input is read-only."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--about', action='store_true',
                    help='show ZX-UX attribution and the ROM reference')
    ap.add_argument('tap', type=Path, nargs='?', help='preserved TAP input')
    ap.add_argument('-o', '--output', type=Path,
                    help='single-tape BAS path (stdout if omitted)')
    ap.add_argument('--program-index', type=int, default=None,
                    help='zero-based BASIC program on tape')
    args = ap.parse_args(argv)
    if args.about:
        print('zx-tap2bas — ZX-UX Spectrum 48K ROM LLIST BASIC exporter')
        print('Based on original work by Supratim Sanyal of SANYALnet Labs.')
        print('Copyright (c) 2026 Supratim Sanyal of SANYALnet Labs.')
        print('License: see ZX-UX repository LICENSE.')
        print('Reference: Sinclair Spectrum 48K ROM LLIST/OUT-LINE/PO-TOKENS.')
        return 0
    if args.tap is None:
        ap.error('specify one TAP input')
    try:
        content = listing(args.tap.read_bytes(), program_index=args.program_index)
        if args.output is None:
            sys.stdout.write(content)
        else:
            _write_listing(args.output, content, (args.tap,))
            print(f'Listed {len(content.splitlines())} BASIC lines into {args.output}',
                  file=sys.stderr)
    except (OSError, TapeError, UnicodeError) as exc:
        print(f'zx-tap2bas: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
