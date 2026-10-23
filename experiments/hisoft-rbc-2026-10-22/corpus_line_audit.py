#!/usr/bin/env python3
"""Read preserved Sinclair tape files and report unresolved literal line jumps.

This check does not alter the tapes or infer omitted BASIC statements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def tape_blocks(tzx: bytes) -> list[bytes]:
    if not tzx.startswith(b'ZXTape!\x1a') or len(tzx) < 10:
        raise ValueError('invalid TZX header')
    blocks = []
    pos = 10
    while pos < len(tzx):
        kind = tzx[pos]
        pos += 1
        if kind == 0x10:
            if pos + 4 > len(tzx):
                raise ValueError('short TZX record')
            _, size = struct.unpack_from('<HH', tzx, pos)
            pos += 4
            if pos + size > len(tzx):
                raise ValueError('truncated TZX record')
            block = tzx[pos:pos + size]
            pos += size
            if len(block) < 2 or not _valid_checksum(block):
                raise ValueError('invalid tape checksum')
            blocks.append(block)
        elif kind == 0x30:
            if pos >= len(tzx):
                raise ValueError('short text record')
            size = tzx[pos]
            pos += 1 + size
        elif kind == 0x32:
            if pos + 2 > len(tzx):
                raise ValueError('short archive record')
            size = struct.unpack_from('<H', tzx, pos)[0]
            pos += 2 + size
        else:
            raise ValueError(f'unsupported TZX block 0x{kind:02x}')
        if pos > len(tzx):
            raise ValueError('truncated extra record')
    return blocks


def _valid_checksum(block: bytes) -> bool:
    value = 0
    for b in block:
        value ^= b
    return value == 0


def basic_lines(tzx: bytes) -> dict[int, bytes]:
    blocks = tape_blocks(tzx)
    for index, block in enumerate(blocks):
        # The 19-byte Sinclair program header carries the payload size.
        if len(block) != 19 or block[:2] != b'\x00\x00':
            continue
        if index + 1 >= len(blocks):
            continue
        next_block = blocks[index + 1]
        if next_block[:1] != b'\xff':
            continue
        size = struct.unpack_from('<H', block, 12)[0]
        data = next_block[1:-1]
        if len(data) != size:
            raise ValueError('BASIC length does not match tape header')
        lines = {}
        pos = 0
        while pos < len(data):
            if pos + 4 > len(data):
                raise ValueError('truncated BASIC line header')
            number = struct.unpack_from('>H', data, pos)[0]
            length = struct.unpack_from('<H', data, pos + 2)[0]
            pos += 4
            if length == 0 or pos + length > len(data):
                raise ValueError(f'invalid BASIC line {number}')
            body = data[pos:pos + length]
            pos += length
            if not body.endswith(b'\r') or number in lines:
                raise ValueError(f'bad BASIC line {number}')
            lines[number] = body
        return lines
    raise ValueError('no ordinary Sinclair BASIC program block found')


def literal_jumps(lines: dict[int, bytes]) -> list[dict[str, int | str]]:
    """Find constant GO TO and GO SUB targets, ignoring quotes and REM text."""
    known = set(lines)
    missing = []
    for number, body in sorted(lines.items()):
        pos = 0
        quoted = False
        while pos < len(body):
            c = body[pos]
            if c == 0x22:
                quoted = not quoted
            if not quoted and c == 0xEA:
                break
            if not quoted and c in (0xEC, 0xED):
                end = pos + 1
                while end < len(body) and body[end] == 0x20:
                    end += 1
                start = end
                while end < len(body) and 0x30 <= body[end] <= 0x39:
                    end += 1
                if end > start:
                    target = int(body[start:end].decode('ascii'))
                    if target not in known:
                        missing.append({'line': number,
                                        'operation': 'GO TO' if c == 0xEC else 'GO SUB',
                                        'target': target})
            if not quoted and c == 0x0E:
                pos += 6
            else:
                pos += 1
    return missing


def inspect(root: Path) -> dict:
    rows = []
    for path in sorted(root.glob('*/BASIC/*.tzx')):
        raw = path.read_bytes()
        row = {'file': str(path.relative_to(root)),
               'sha256': hashlib.sha256(raw).hexdigest()}
        try:
            lines = basic_lines(raw)
            row['line_count'] = len(lines)
            row['missing_literal_targets'] = literal_jumps(lines)
            row['status'] = 'parsed'
        except ValueError as exc:
            row['status'] = 'unreadable'
            row['reason'] = str(exc)
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise RuntimeError('source tape unexpectedly changed')
        rows.append(row)
    return {'programs': len(rows),
            'parsed': sum(row['status'] == 'parsed' for row in rows),
            'missing_target_programs': sum(bool(row.get('missing_literal_targets'))
                                           for row in rows),
            'rows': rows}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root', type=Path, help='original 60-program directory')
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    report = inspect(args.root)
    for row in report['rows']:
        missing = row.get('missing_literal_targets', [])
        if missing:
            print(row['file'], missing)
        if row['status'] != 'parsed':
            print(row['file'], row['status'], row['reason'])
    print('TAPES', report['programs'], 'PARSED', report['parsed'],
          'MISSING-TARGET-PROGRAMS', report['missing_target_programs'])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    if report['programs'] != 60:
        raise SystemExit('expected 60 source tapes')


if __name__ == '__main__':
    main()
