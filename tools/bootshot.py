#!/usr/bin/env python3
"""Capture the ZX-UX v1 login screen from a real ROM tape boot snapshot.

Requires build/test.z80 from the checked SkoolKit 48K ROM tape loader.
Writes a pixel-doubled screenshot of the 256 by 192 Spectrum display.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
for folder in ('tools', 'sdk', 'tests'):
    sys.path.insert(0, str(ROOT / folder))
import rvm
import suite


def main():
    session = suite.Session(str(ROOT / 'build' / 'test.z80'))
    session.zx.run(120)
    screen = session.screen()
    if 'login:' not in screen or 'ZX-UX UNIX v1' not in screen:
        raise SystemExit('The expected v1 login screen did not appear')
    output = ROOT / 'build' / 'proofs'
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'boot-rom.png'
    ram = bytes(session.zx.mem[0x4000:0x5B00])
    if len(ram) != 6912:
        raise SystemExit('Invalid Spectrum display memory')
    rvm.write_png(ram, str(path), session.zx.tr.border)
    print('ROM tape boot:', path.relative_to(ROOT))


if __name__ == '__main__':
    main()
