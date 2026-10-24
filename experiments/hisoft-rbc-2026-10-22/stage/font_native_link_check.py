"""Prove actual HiSoft code links to a process-owned Sinclair font SSX1."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys


def check(root: Path) -> None:
    root = root.resolve()
    scratch = root / 'build/tmp/rbc-round2'
    compiler = scratch / 'current/rbc/rbc.py'
    upstream = scratch / 'upstream'
    tape = scratch / 'hisoft48.tap'
    sdk = root / 'src/zx-ux-sdk'
    rom = sdk / 'rom/48.rom'
    if not all(p.is_file() for p in (compiler, upstream/'compiler.py',tape,rom)):
        raise RuntimeError('The frozen HiSoft native toolchain is unavailable')
    # The high RAM byte is written before CHARS points at this font, as in
    # historic custom charset listings. The private alias must not rely on
    # source rewriting or on executing the original program to be linked.
    source = scratch / 'private-font-fixture.bas'
    output = scratch / 'private-font-fixture.ssx'
    report = scratch / 'private-font-fixture.json'
    source.write_text('10 POKE 60256,170\n'
                      '20 POKE 23606,96\n'
                      '30 POKE 23607,235\n'
                      '40 PRINT PEEK 60256\n'
                      '50 POKE 23606,0\n'
                      '60 POKE 23607,60\n'
                      '70 STOP\n',encoding='ascii')
    output.unlink(missing_ok=True)
    env = dict(os.environ, PYTHONPATH=str(upstream))
    cmd = [sys.executable,str(compiler),str(source),
           '--frontend',str(upstream),'--tape',str(tape),'--rom',str(rom),
           '--sdk',str(sdk),'-o',str(output),'--report',str(report)]
    result = subprocess.run(cmd, env=env, cwd=root, capture_output=True,text=True)
    if result.returncode or not output.is_file() or not report.is_file():
        raise RuntimeError('Native custom-font SSX did not link: '
                           + result.stderr + result.stdout)
    meta = json.loads(report.read_text())
    if meta.get('private_font_alias') != 60256 or meta.get('font_source') != 'process_image' or meta.get('font_bytes') != 1024:
        raise RuntimeError('Native custom-font SSX is missing process-private 1024-byte glyph bank')
    sys.path.insert(0,str(sdk))
    import rld
    binary=output.read_bytes()
    image=rld.parse_ssx(binary)
    if not binary.startswith(b'SSX1') or not image['relocs']:
        raise RuntimeError('Native custom-font SSX linker format is invalid')
    if meta.get('bss') != image['bss'] or image['bss'] < 14:
        raise RuntimeError('Native private CHARS virtual state is not allocated')
    print('RBC native font SSX PASS:',len(binary),'bytes')


if __name__=='__main__':
    check(Path(__file__).resolve().parents[3])
