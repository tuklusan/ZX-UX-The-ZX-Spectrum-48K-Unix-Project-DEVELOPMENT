#!/usr/bin/env python3
"""Compile the LM C48 source with the current ZX-UX SDK only.

An image larger than the 48K loader limit is not native execution proof.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'sdk'))
import rld  # noqa: E402
import rtap  # noqa: E402
from rcc import driver  # noqa: E402


def main():
    source = ROOT / 'programs/c48/ailmzx48/ailmzx48.c'
    output = ROOT / 'build/lm/ailmzx48.ssx'
    if not source.is_file():
        raise RuntimeError('LM C48 source missing')
    output.parent.mkdir(parents=True, exist_ok=True)
    if driver.main([str(source), '-o', str(output)]):
        raise RuntimeError('LM compilation failed')
    binary = output.read_bytes()
    info = rld.parse_ssx(binary)
    needed = rtap.need(binary)
    if not binary.startswith(b'SSX1') or not info['image'] or needed < len(binary):
        raise RuntimeError('LM did not produce a valid v1 SSX1 image')
    print('PASS LM current SDK: SSX1 file %d bytes, need %d bytes, v1 limit %d bytes' %
          (len(binary), needed, driver.ZXUX_MAX))
    if needed > driver.ZXUX_MAX:
        print('LM exceeds the configured v1 loader memory budget; native execution not claimed')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError) as error:
        print('FAIL LM:', error, file=sys.stderr)
        sys.exit(1)
