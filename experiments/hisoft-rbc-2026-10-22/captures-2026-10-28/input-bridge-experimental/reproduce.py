#!/usr/bin/env python3
"""One genuine ZX-UX framebuffer per original BAS, research INPUT bridge only.

The input adapter is used solely as a witnessed pre-link source experiment;
published binaries and numbered BASIC originals are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
TESTS = ROOT / 'experiments/hisoft-rbc-2026-10-22/tests'
sys.path[:0] = [str(STAGE), str(TESTS), str(ROOT / 'src/zx-ux-sdk')]
import rld
import rvm
from zxscreen import write_png
from native_rbc_cli import compile_native
from test_native_input_bridge_candidate import link_candidate

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
GAMES = ROOT / 'src/bonus/60-programs'

CASE = {
    '23-biorhythms': (
        '{WAIT 100}1980{ENTER}{WAIT 30}10{ENTER}{WAIT 30}28{ENTER}'
        '{WAIT 30}2026{ENTER}{WAIT 30}10{ENTER}{WAIT 30}28{ENTER}', 1500),
    '56-roots': ('{WAIT 300}{ENTER}{WAIT 200}{ENTER}{WAIT 200}{ENTER}', 1550),
    '07-critical-path-analysis': (
        '{WAIT 300}{ENTER}{WAIT 220}{ENTER}{WAIT 180}1{ENTER}'
        '{WAIT 130}12{ENTER}', 1800),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', choices=sorted(CASE))
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    output = a.output.resolve()
    allowed = (Path(__file__).resolve().parent,
               ROOT / 'build/tmp/rbc-round2')
    if not any(output.is_relative_to(d.resolve()) for d in allowed):
        raise ValueError('experimental PNG output must stay in experiment/build area')
    if SYSTEM.read_bytes() != FROZEN.read_bytes():
        raise ValueError('rebuilt ZX-UX tape differs from the frozen release')
    original = GAMES / a.game / 'BASIC' / (a.game + '.bas')
    published = GAMES / a.game / 'bin' / (a.game + '.ssx')
    bas_bytes, original_ssx = original.read_bytes(), published.read_bytes()
    asm, obj, reference, proof = compile_native(original, CHECKPOINT,
                                                 FRONTEND, TAPE, ROM)
    if (not obj.startswith(b'SSO1') or reference != original_ssx or
            not proof['native_three_base_source_verified'] or
            not proof['native_and_legacy_ssx_byte_identical'] or
            proof['optimizer_used']):
        raise ValueError('original native assembly fails strict three-base check')
    linked = link_candidate(asm)
    image = rld.parse_ssx(linked)
    total = len(image['image']) + image['bss'] + image['stack']
    if max(total, len(linked)) > 14000 or image['entry'] != 0:
        raise ValueError('experimental native INPUT exceeds loader admission')
    keys, frames = CASE[a.game]
    with tempfile.TemporaryDirectory(prefix='rbc-experimental-input-') as tmp:
        scratch = Path(tmp) / (a.game + '.ssx')
        scratch.write_bytes(linked)
        run = rvm.run_kernel(scratch, keys=keys, frames=frames, system=SYSTEM)
        if run.fg.started is None or run.why not in ('input', 'frames', 'exit'):
            raise ValueError('real ZX-UX did not run original BASIC game')
        display, border = run.picture()
        if len(display) != 6912:
            raise ValueError('missing original Spectrum 48K framebuffer')
        if run.fg.ended is not None:
            if run.fg.status != 0 or run.session.owns_screen(run.fg.pid):
                raise ValueError('native exit did not restore ZX-UX shell ownership')
        if original.read_bytes() != bas_bytes or published.read_bytes() != original_ssx:
            raise ValueError('original game bytes unexpectedly modified')
        a.output.parent.mkdir(parents=True, exist_ok=True)
        write_png(display, a.output, border)
    print(f'{a.game}: genuine ZX-UX screen why={run.why} '
          f'original_BAS_sha256={sha(bas_bytes)} '
          f'original_published_SSX_sha256={sha(original_ssx)} '
          f'experimental_input_SSX_sha256={sha(linked)} '
          f'framebuffer_sha256={sha(display)} '
          f'png_sha256={sha(a.output.read_bytes())} '
          f'file={len(linked)} image={len(image["image"])} '
          f'bss={image["bss"]} stack={image["stack"]} total={total}')


if __name__ == '__main__':
    main()
