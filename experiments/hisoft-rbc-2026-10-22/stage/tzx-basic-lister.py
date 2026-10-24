#!/usr/bin/env python3
"""List Sinclair Spectrum 48K BASIC from TZX tapes using ROM LIST spacing.

This standalone reader does not edit the tape or any original BASIC listing.
The 48K ROM's token table at 0096h supplies the spelling of each keyword.
Spacing follows PO_SEARCH/PO_TABLE (0C41h/0C14h), PO_CHAR (0B65h),
OUT_LINE/OUT_CHAR (1855h/1937h) and PO_TOKENS (0C10h).

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
    """Read the actual ROM's bit-7-terminated keyword table, 0096h onwards."""
    if len(rom) != 16384 or rom[0x95] != 0xbf:
        raise TapeError('expected a standard 16 KiB Spectrum 48K ROM keyword table')
    words = {}
    pos = 0x96
    for token in range(0xa5, 0x100):
        word = bytearray()
        while True:
            if pos >= len(rom):
                raise TapeError('truncated ROM keyword table')
            ch = rom[pos]
            pos += 1
            word.append(ch & 127)
            if ch & 128:
                break
            if len(word) > 40:
                raise TapeError('invalid ROM keyword length')
        if not word or any(not 32 <= c < 127 for c in word):
            raise TapeError(f'invalid ROM keyword {token:02X}')
        words[token] = bytes(word)
    if words[0xa5] != b'RND' or words[0xcb] != b'THEN' or words[0xff] != b'COPY':
        raise TapeError('unexpected ROM keyword sequence')
    return words


def list_line(number: int, body: bytes, tokens: dict[int, bytes]) -> str:
    """ROM OUT_LINE/PO_SEARCH spacing, with safe ASCII escapes for glyphs.

    The ROM prints a four-character line number and a space. It tracks bit 0
    of FLAGS: a printed space suppresses the *next* token's optional leading
    space. RND, INKEY$ and PI do not acquire their usual trailing space.
    """
    result = [f'{number:4d}']
    # OUT_LINE resets FLAGS.0 after printing the four-column number.
    suppress_lead = False
    quoted = rem = in_data = False
    i = 0
    while i < len(body):
        c = body[i]
        if c == 14 and not (quoted or rem):
            if i + 6 > len(body):
                raise TapeError(f'Line {number}: truncated five-byte numeric value at offset {i}')
            i += 6  # ROM NUMBER (18B6h), even inside string/REM.
            continue
        if c == 34 and not rem:
            quoted = not quoted
        if c == 58 and not quoted and not rem:
            in_data = False
        if c >= 0xa5 and (quoted or rem or in_data):
            # The screen LIST expands these too. In a *source file* that
            # would destroy the byte when re-imported, so emit its escape.
            result.append('{' + f'{c:02X}' + '}')
            suppress_lead = False
            i += 1
            continue
        if c >= 0xa5:
            if c == 0xea:
                rem = True
            if c == 0xe4:
                in_data = True
            word = tokens[c]
            tnum = c - 0xa5
            # ROM PO_SEARCH: index < 32 suppresses leading space;
            # otherwise the token text must begin with A or later.
            if tnum >= 32 and word[0] >= ord('A') and not suppress_lead:
                result.append(' ')
            result.append(word.decode('ascii'))
            suppress_lead = False
            # ROM PO_TOKENS tests the final original table character's
            # high bit and subtracts: '$' or letter ending => trailing
            # space except for the first three tokens (RND/INKEY$/PI).
            if tnum >= 3 and (word.endswith(b'$') or word[-1] >= ord('A')):
                result.append(' ')
                suppress_lead = True
            i += 1
            continue
        if 32 <= c <= 126 and c not in (123, 125):
            ch = chr(c) if c != 96 else '{60}'  # Spectrum code 60h is pound sign
            result.append(ch)
            suppress_lead = c == 32
        else:
            # Raw Spectrum bytes require a reversible ASCII notation. Literal
            # braces must be escaped so {HH} in a string is never mistaken for
            # an expansion when importing with BAS2TAP.
            result.append('{' + f'{c:02X}' + '}')
            if c in (123, 125) or 0x7f <= c <= 0xa4:
                suppress_lead = False
        i += 1
    if quoted:
        raise TapeError(f'Line {number}: unterminated quoted string')
    return ''.join(result)


def listing(tape: bytes, rom: bytes, *, program_index: int | None = None) -> str:
    words = rom_keywords(rom)
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
    result = [list_line(n, body, words) for n, body in numbered_lines(program)]
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
