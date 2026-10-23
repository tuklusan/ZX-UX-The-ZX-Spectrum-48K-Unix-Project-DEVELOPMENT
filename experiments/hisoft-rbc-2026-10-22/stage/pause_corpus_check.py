#!/usr/bin/env python3
"""Check safe PAUSE 0 transformations across unchanged original BASIC tapes.

This is a tokenized-source preparation check, not a HiSoft compilation run.
Both the input tapes and their associated text listings remain read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

from pause_zero import rewrite_pause_zero


def _rows(program: bytes):
    rows = []
    pos = 0
    while pos < len(program):
        if pos + 4 > len(program):
            raise ValueError('short BASIC line header')
        number = int.from_bytes(program[pos:pos + 2], 'big')
        size = int.from_bytes(program[pos + 2:pos + 4], 'little')
        body = program[pos + 4:pos + 4 + size]
        if size == 0 or len(body) != size or not body.endswith(b'\r'):
            raise ValueError(f'invalid BASIC line {number}')
        rows.append((number, body))
        pos += 4 + size
    return rows


def _join(rows):
    out = bytearray()
    for number, body in rows:
        out.extend(number.to_bytes(2, 'big'))
        out.extend(len(body).to_bytes(2, 'little'))
        out.extend(body)
    return bytes(out)


def inspect(root: Path):
    tool_path = root / 'TOOLS'
    sys.path.insert(0, str(tool_path))
    try:
        from zx_basic_tape import TOKENS, encode_body, find_basic, parse_standard_tzx
    finally:
        sys.path.remove(str(tool_path))
    words = {word: code for code, word in TOKENS.items()}
    fake_tap = types.ModuleType('tap')
    fake_tap.split_lines = _rows
    fake_tap.join_lines = _join
    fake_source = types.ModuleType('source')
    fake_source.tokenize_line = lambda text, kw: encode_body(text)
    fake_source.hide_numbers = lambda body, fp: body
    keys = types.SimpleNamespace(CODE_FOR=words)
    report = []
    tapes = sorted(root.glob('*/BASIC/*.tzx'))
    with patch.dict(sys.modules, {'tap': fake_tap, 'source': fake_source}):
        for path in tapes:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            programs = find_basic(parse_standard_tzx(raw))
            if not programs:
                raise ValueError(f'{path.name}: no tokenized BASIC program')
            original = programs[0][1]
            temporary, changes = rewrite_pause_zero(original, keys, None)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError(f'source file changed during check: {path}')
            report.append({
                'game': path.parent.parent.name,
                'tape_sha256': digest,
                'source_bytes_unchanged': True,
                'source_line_count': len(_rows(original)),
                'temporary_line_count': len(_rows(temporary)),
                'wait_rewrites': changes,
            })
    return {
        'source_tapes': len(report),
        'programs_with_safe_wait_rewrites': sum(bool(x['wait_rewrites']) for x in report),
        'safe_wait_rewrites': sum(len(x['wait_rewrites']) for x in report),
        'source_bytes_unchanged': all(x['source_bytes_unchanged'] for x in report),
        'programs': report,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('original_programs', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = inspect(args.original_programs)
    print('TAPES', result['source_tapes'], 'PROGRAMS WITH WAITS',
          result['programs_with_safe_wait_rewrites'], 'REWRITES',
          result['safe_wait_rewrites'])
    if result['source_tapes'] != 60 or not result['source_bytes_unchanged']:
        raise SystemExit('expected 60 unmodified original BASIC tapes')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
