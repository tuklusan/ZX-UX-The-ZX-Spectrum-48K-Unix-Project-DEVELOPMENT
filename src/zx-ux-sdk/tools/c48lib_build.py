#!/usr/bin/env python3
"""Assemble rb2ct C48 support into lib/c48lib.ssa (separate from libc48.ssa)."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ras, rld

def build(sdk=ROOT):
    sdk = Path(sdk)
    source = sdk / 'rb2ct/c48lib'
    objects = []
    for filename in ('c48lib.asm', 'c48lib-font.asm'):
        path = source / filename
        asm = path.read_text(encoding='utf-8')
        if filename == 'c48lib-font.asm':
            asm = '        global c48_vga_font\n' + asm
        objects.append((path.stem + '.sso', ras.assemble_text(asm, str(path))))
    out = sdk / 'lib/c48lib.ssa'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(rld.write_archive(objects))
    return out

if __name__ == '__main__':
    print(build())
