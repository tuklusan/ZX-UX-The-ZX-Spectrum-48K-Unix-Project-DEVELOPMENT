#!/usr/bin/env python3
"""List Sinclair Spectrum 48K BASIC from TZX tapes using ROM LLIST.

This standalone reader does not edit the tape or any original BASIC listing.
The 48K ROM's token table at 0096h supplies the spelling of each keyword.
This is a direct translation of the shared LLIST/ LIST source code path:
17F5/17FB, 1855, 18B6, 1937, 0C10, 0C41, 0C22, 0C35 and 0B65.
The actual 48K ROM supplies the complete token table, including its bit-7
terminators. Use llist_codes() for the literal pre-printer character stream.

The output is an ASCII source representation, not a pixel-perfect recreation
of the LIST screen. Non-ASCII character and control bytes use BAS2TAP's {HH}
escapes. Numeric cache bytes (0Eh plus five bytes) are omitted as ROM LIST
omits them. For byte-exact archival preservation always retain the TZX.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


class TapeError(ValueError):
    """The source tape is malformed, ambiguous, or unsupported."""


def _take(data: bytes, offset: int, size: int, what: str) -> tuple[bytes, int]:
    if size < 0 or offset + size > len(data):
        raise TapeError(f'{what}: truncated at offset {offset}')
    return data[offset:offset + size], offset + size


def _u16(data: bytes, at: int) -> int:
    return int.from_bytes(data[at:at + 2], 'little')


def _u24(data: bytes, at: int) -> int:
    return int.from_bytes(data[at:at + 3], 'little')


def _u32(data: bytes, at: int) -> int:
    return int.from_bytes(data[at:at + 4], 'little')


def tzx_blocks(tape: bytes):
    """Extract data-bearing TZX tape blocks; reject unknown/branched formats.

    Standard (10), turbo (11), and pure data (14) bytes represent normal TAP
    bytes when used with full 8-bit final data. Audio-only encoding cannot be
    identified as a stored ZX BASIC program without demodulation and is never
    silently treated as one.
    """
    if not tape.startswith(b'ZXTape!\x1a') or len(tape) < 10:
        raise TapeError('missing TZX signature')
    if tape[8] != 1:
        raise TapeError(f'unsupported TZX major version {tape[8]}')
    pos = 10
    while pos < len(tape):
        start = pos
        kind = tape[pos]
        pos += 1
        if kind == 0x10:  # standard speed: pause, u16 data length
            info, pos = _take(tape, pos, 4, 'standard-speed block')
            payload, pos = _take(tape, pos, _u16(info, 2), 'standard-speed payload')
        elif kind == 0x11:  # turbo: 15 timing bytes, u24 data length
            info, pos = _take(tape, pos, 18, 'turbo block')
            if info[12] != 8:
                raise TapeError(f'turbo block at {start}: non-byte-aligned last byte')
            payload, pos = _take(tape, pos, _u24(info, 15), 'turbo payload')
        elif kind == 0x14:  # pure data: two pulse lengths, used bits, pause, size
            info, pos = _take(tape, pos, 10, 'pure-data block')
            if info[4] != 8:
                raise TapeError(f'pure-data block at {start}: non-byte-aligned last byte')
            payload, pos = _take(tape, pos, _u24(info, 7), 'pure-data payload')
        elif kind in (0x20, 0x23, 0x24, 0x2A):  # pause, jump, loop start, stop 48K
            if kind != 0x20:
                raise TapeError(f'control-flow block {kind:02X} at {start}: cannot flatten faithfully')
            size = 2
            info, pos = _take(tape, pos, size, f'block {kind:02X}')
            if kind == 0x20 and _u16(info, 0) == 0:
                raise TapeError(f'stop-tape block at {start}: playback sequence ambiguous')
        elif kind in (0x21, 0x30):
            info, pos = _take(tape, pos, 1, f'block {kind:02X}')
            _, pos = _take(tape, pos, info[0], f'block {kind:02X} text')
        elif kind == 0x22:  # group end
            pass
        elif kind == 0x31:  # message: duration + length
            info, pos = _take(tape, pos, 2, 'message')
            _, pos = _take(tape, pos, info[1], 'message text')
        elif kind in (0x28, 0x32):  # selection or archive info: u16 payload
            info, pos = _take(tape, pos, 2, 'metadata length')
            if kind == 0x28:
                raise TapeError(f'select block at {start}: playback sequence ambiguous')
            _, pos = _take(tape, pos, _u16(info, 0), 'archive information')
        elif kind == 0x33:  # hardware info: count * 3
            info, pos = _take(tape, pos, 1, 'hardware information')
            _, pos = _take(tape, pos, info[0] * 3, 'hardware entries')
        elif kind == 0x35:  # custom info: 16-byte id + u32 length
            info, pos = _take(tape, pos, 20, 'custom info')
            _, pos = _take(tape, pos, _u32(info, 16), 'custom info body')
        elif kind == 0x5A:  # TZX concatenation marker
            marker, pos = _take(tape, pos, 9, 'TZX glue')
            if marker[:8] != b'XTape!\x1a\x01':
                raise TapeError(f'invalid TZX glue at {start}')
        else:
            raise TapeError(f'unsupported TZX block type {kind:02X} at offset {start}')
        if kind in (0x10, 0x11, 0x14):
            if len(payload) < 2:  # flag byte and XOR parity byte
                raise TapeError(f'block {kind:02X} at {start}: short tape block')
            check = 0
            for byte in payload:
                check ^= byte
            if check:
                raise TapeError(f'block {kind:02X} at {start}: TAP XOR checksum mismatch')
            yield payload


def basic_programs(tape: bytes):
    """Yield (10-byte header name, tokenized BASIC) from header/data pairs."""
    pending = None
    for block in tzx_blocks(tape):
        if block[0] == 0 and len(block) == 19:
            # Format: flag, type, 10-byte name, length, autostart, vars, XOR.
            if pending:
                raise TapeError('new header before previous BASIC data')
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
            # BAS2TAP headers normally have vars-offset == program length.
            # A real tape may contain variables after BASIC lines; use header.
            yield name, program[:vars_offset]
    if pending:
        raise TapeError('missing BASIC data block after header')


def numbered_lines(program: bytes):
    p = 0
    last = -1
    while p < len(program):
        header, p = _take(program, p, 4, 'BASIC line header')
        number = int.from_bytes(header[:2], 'big')
        size = _u16(header, 2)
        if not 0 <= number <= 9999 or number <= last:
            raise TapeError(f'BASIC line numbers out of order: {last}, {number}')
        if size == 0:
            raise TapeError(f'Line {number}: zero-length BASIC line')
        contents, p = _take(program, p, size, f'Line {number}')
        if contents[-1] != 13:
            raise TapeError(f'Line {number}: no end-of-line marker')
        last = number
        yield number, contents[:-1]
    if p != len(program):
        raise TapeError('BASIC program does not end on a line boundary')


def rom_keywords(rom: bytes) -> dict[int, bytes]:
    """Expose the 91 ROM-table entries without spelling a keyword in Python."""
    return {0xA5 + n: word for n, (word, _, _) in enumerate(_rom_token_entries(rom))}


def llist_segments(number: int, body: bytes, rom: bytes):
    """Translate the ROM LLIST character-output path (excluding printer pixels).

    17F5 LLIST -> 17FB LIST-1 -> 1833 LIST-ALL -> 1855 OUT-LINE:
    1A28 OUT-NUM-2 emits a four-column number; 1874 resets FLAGS.0.
    18A5/18B6 NUMBER skips the five-byte numeric representation.
    1937 OUT-CHAR sends each source code to RST 10.
    0B52 PO-T-UDG routes A5..FF to 0C10 PO-TOKENS.
    0C41 PO-SEARCH checks index and original first ROM table byte.
    0C22 PO-EACH reads and emits characters until high-bit termination.
    0C2D..0C39 PO-TR-SP determines whether to add a trailing space.
    0B65 PO-CHAR resets FLAGS.0 for ordinary printable characters and sets
    it for space; nonprintable/UDG codes do not alter that flag.

    Each result is (emitted bytes, original BASIC byte, token expansion flag).
    No keyword spelling, whitespace or lexical boundary is inferred.
    """
    if not 0 <= number <= 9999:
        raise TapeError(f'invalid BASIC line number {number}')
    token_entries = _rom_token_entries(rom)
    # OUT-NUM-2/OUT-SP-NO: number is printed in four columns.
    parts = [(f'{number:4d}'.encode('ascii'), None, False)]
    # OUT-LINE at 1874 sets FLAGS.0 to permit a leading space.
    flags_0 = False

    def emit(byte: int) -> None:
        nonlocal flags_0
        # 0B65 PO-CHAR: only ordinary printable characters alter FLAGS.0;
        # characters less than 20h are dispatched as printer controls.
        if 32 <= byte < 128:
            flags_0 = (byte == 32)

    p = 0
    while p < len(body):
        value = body[p]
        if value == 14:  # 18B6 NUMBER: skip its full hidden five-byte form.
            if p + 6 > len(body):
                raise TapeError(f'Line {number}: truncated five-byte numeric value at offset {p}')
            p += 6
            continue
        if value < 0xA5:
            emit(value)
            parts.append((bytes([value]), value, False))
        else:
            index = value - 0xA5
            word, first, last = token_entries[index]
            out = bytearray()
            # 0C41: carry set for 00..1F; otherwise subtract 'A' from
            # the *original* first (possibly high-bit-set) table byte.
            if index >= 0x20 and first >= 0x41 and not flags_0:
                out.append(32)
                emit(32)
            for character in word:
                out.append(character)
                emit(character)
            # 0C2A doubles the last original byte and tests 48h ('$')
            # or >=82h ('A' through letters); index 0..2 never follows.
            last_doubled = (last << 1) & 255
            if index >= 3 and (last_doubled == 0x48 or last_doubled >= 0x82):
                out.append(32)
                emit(32)
            parts.append((bytes(out), value, True))
        p += 1
    return parts


def _rom_token_entries(rom: bytes) -> list[tuple[bytes, int, int]]:
    """Read 0C10's exact bit-7-terminated ROM table at 0096h, including ends.

    0C41 starts scanning from 0095h, the byte immediately before RND.
    The scanner advances to the following byte after the terminator.
    """
    if len(rom) != 0x4000 or rom[0x95] != 0xBF:
        raise TapeError('expected a standard 16 KiB Spectrum 48K ROM keyword table')
    pos = 0x96
    out = []
    for token in range(0xA5, 0x100):
        start = pos
        while pos < len(rom) and not (rom[pos] & 128):
            pos += 1
        if pos >= len(rom) or pos - start > 40:
            raise TapeError(f'ROM keyword {token:02X} has no valid high-bit terminator')
        raw = rom[start:pos + 1]
        pos += 1
        word = bytes(c & 0x7f for c in raw)
        if not word or any(not 32 <= c < 127 for c in word):
            raise TapeError(f'ROM keyword {token:02X} contains invalid characters')
        out.append((word, raw[0], raw[-1]))
    if out[0][0] != b'RND' or out[0xCB-0xA5][0] != b'THEN' or out[-1][0] != b'COPY':
        raise TapeError('unexpected 48K ROM keyword sequence')
    return out


def llist_codes(number: int, body: bytes, rom: bytes) -> bytes:
    """ROM LLIST emitted character codes, prior to printer bitmap wrapping.

    The physical ZX Printer represents characters as dots in 32-column rows;
    this logical code stream is the relevant output for BASIC regeneration.
    """
    return b''.join(output for output, _, _ in llist_segments(number, body, rom))


def list_line(number: int, body: bytes, rom: bytes) -> str:
    """Safely serialize the ROM LLIST listing into BAS2TAP-compatible ASCII.

    ROM LLIST's *exact* emitted character stream is available via llist_codes.
    This adapter alone escapes bytes which ROM's printer cannot transcribe
    reversibly: graphics/controls, braces, the Spectrum pound glyph, and
    keyword bytes originally inside quoted literals, REM or DATA. It never
    alters the ROM's keyword spacing decisions. TZX remains authoritative.
    """
    parts = llist_segments(number, body, rom)
    quoted = rem = data = False
    rendered = []
    for segment, original, expanded in parts:
        if original is None:
            rendered.append(segment.decode('ascii'))
            continue
        if expanded:
            if quoted or rem or data:
                # The actual printer expands the token regardless of mode.
                # Keep original bytes instead of corrupting a string/REM/DATA.
                rendered.append(f'{{{original:02X}}}')
            else:
                rendered.append(segment.decode('ascii'))
            if not quoted and not rem and original == 0xEA:
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


def listing(tape: bytes, rom: bytes, *, program_index: int | None = None) -> str:
    _rom_token_entries(rom)
    programs = list(basic_programs(tape))
    if not programs:
        raise TapeError('TZX contains no Spectrum BASIC program header/data pair')
    if program_index is None:
        if len(programs) != 1:
            raise TapeError(f'TZX contains {len(programs)} BASIC programs; specify --program-index')
        program_index = 0
    if not 0 <= program_index < len(programs):
        raise TapeError(f'program index {program_index} outside 0..{len(programs) - 1}')
    name, program = programs[program_index]
    result = [list_line(n, body, rom) for n, body in numbered_lines(program)]
    if not result:
        raise TapeError(f'BASIC program {name!r} has no lines')
    return '\n'.join(result) + '\n'


def _protected_listing_destination(path: Path) -> bool:
    """Never generate into any preserved 60-game BASIC directory."""
    parts = path.resolve().parts
    for i in range(len(parts) - 3):
        if (parts[i:i + 2] == ('bonus', '60-programs')
                and parts[i + 2][:2].isdigit() and parts[i + 3] == 'BASIC'):
            return True
    return False


def _write_listing(path: Path, content: str, inputs: tuple[Path, ...]):
    dest = path.resolve()
    if dest in (p.resolve() for p in inputs) or _protected_listing_destination(dest):
        raise TapeError(f'protected destination: {dest}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('x', encoding='ascii', newline='\n') as f:
        f.write(content)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('tzx', type=Path, nargs='?', help='preserved TZX input')
    ap.add_argument('--corpus', type=Path,
                    help='directory containing all 60 numbered game folders')
    ap.add_argument('--rom', type=Path, required=True,
                    help='original Spectrum 48K 16 KiB ROM image')
    ap.add_argument('-o', '--output', type=Path,
                    help='single-tape BAS path (stdout if omitted)')
    ap.add_argument('--out-dir', type=Path,
                    help='staging directory for --corpus (never the original BASIC tree)')
    ap.add_argument('--program-index', type=int, default=None,
                    help='zero-based BASIC program on tape')
    args = ap.parse_args(argv)
    if bool(args.tzx) == bool(args.corpus):
        ap.error('specify either one TZX or --corpus')
    if args.corpus and (args.output or not args.out_dir):
        ap.error('--corpus requires --out-dir and does not accept --output')
    if args.tzx and args.out_dir:
        ap.error('--out-dir is for --corpus only')
    try:
        rom = args.rom.read_bytes()
        rom_keywords(rom)
        if args.tzx:
            content = listing(args.tzx.read_bytes(), rom,
                              program_index=args.program_index)
            if args.output is None:
                sys.stdout.write(content)
            else:
                _write_listing(args.output, content, (args.tzx, args.rom))
                print(f'Listed {len(content.splitlines())} BASIC lines into {args.output}',
                      file=sys.stderr)
        else:
            root = args.corpus.resolve()
            games = sorted(p for p in root.iterdir()
                           if p.is_dir() and len(p.name) > 3
                           and p.name[:2].isdigit() and p.name[2] == '-')
            if len(games) != 60:
                raise TapeError(f'expected 60 numbered game directories; found {len(games)}')
            out = args.out_dir.resolve()
            planned = []
            for game in games:
                tape = game / 'BASIC' / (game.name + '.tzx')
                dest = out / game.name / 'BASIC' / (game.name + '.bas')
                if _protected_listing_destination(dest) or dest.exists():
                    raise TapeError(f'protected or existing output: {dest}')
                content = listing(tape.read_bytes(), rom,
                                  program_index=args.program_index)
                planned.append((tape, dest, content))
            for tape, dest, content in planned:
                _write_listing(dest, content, (tape, args.rom))
            print(f'Listed 60 TZX programs under {out}', file=sys.stderr)
    except (OSError, TapeError, UnicodeError) as exc:
        print(f'tzx-basic-lister: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
