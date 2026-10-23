#!/usr/bin/env python3
"""Create Spectrum-order printable font rows from a public-domain 8x8 table.

Input is tuklusan/font8x8's font8x8_basic.h. Source rows store the
leftmost pixel in bit zero; ZX Spectrum display rows store it in bit seven.
Only characters U+0020 through U+007F belong in the CHARS table.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re


def build_font(header: str) -> bytes:
    rows = re.findall(r'\{\s*((?:0x[0-9A-Fa-f]{2}\s*,?\s*){8})\}', header)
    if len(rows) != 128:
        raise ValueError(f'expected 128 font characters, found {len(rows)}')
    output = bytearray()
    for glyph in rows[32:128]:
        bytes8 = re.findall(r'0x[0-9A-Fa-f]{2}', glyph)
        if len(bytes8) != 8:
            raise ValueError('font row must contain eight bytes')
        for value in bytes8:
            b = int(value, 16)
            output.append(int(f'{b:08b}'[::-1], 2))
    if len(output) != 768:
        raise ValueError('printable font must have 768 bytes')
    return bytes(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('font_header', type=Path)
    parser.add_argument('output', type=Path)
    opts = parser.parse_args()
    opts.output.write_bytes(build_font(opts.font_header.read_text()))


if __name__ == '__main__':
    main()
