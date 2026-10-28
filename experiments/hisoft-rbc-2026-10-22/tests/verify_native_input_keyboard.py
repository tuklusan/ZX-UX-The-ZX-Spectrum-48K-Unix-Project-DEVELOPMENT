#!/usr/bin/env python3
"""Real native INPUT keyboard proof: currently an explicit failing gate.

Build an original numbered BASIC fixture with the delivered no-optimizer CLI.
Type through the actual Spectrum keyboard in the ZX-UX emulator. No memory
edits, fake input hooks, SSX patching, or synthetic process exits.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
from native_rbc_cli import compile_native
import rvm

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
LISTING = ('10 REM : OPEN #\n20 PRINT "ENTER NAME"\n'
           '30 INPUT A$\n40 PRINT A$\n50 STOP\n')


def main():
    if SYSTEM.read_bytes() != FROZEN.read_bytes():
        raise ValueError('system tape changed from frozen ZX-UX release')
    with tempfile.TemporaryDirectory(prefix='rbc-native-input-') as folder:
        path = Path(folder)
        source = path / 'input.bas'
        linked = path / 'input.ssx'
        source.write_text(LISTING, encoding='ascii')
        _, obj, ssx, report = compile_native(
            source, CHECKPOINT, FRONTEND, TAPE, ROM)
        if (not obj.startswith(b'SSO1') or
                not report['native_three_base_source_verified'] or
                not report['native_and_legacy_ssx_byte_identical'] or
                report['optimizer_used']):
            raise ValueError('native INPUT source or linker gate rejected')
        linked.write_bytes(ssx)
        runner = rvm.run_kernel(linked, keys='{WAIT 200}abc{ENTER}',
                                frames=1100, system=SYSTEM)
        if runner.fg.started is None:
            raise ValueError('ZX-UX never started native INPUT program')
        if runner.why != 'exit' or runner.fg.status != 0:
            print('INPUT NOT VERIFIED: native process did not exit; '
                  f'why={runner.why}, LAST_K={runner.session.m.mem[0x5c08]}, '
                  f'FLAGS={runner.session.m.mem[0x5c3b]:02x}', flush=True)
            return 1
        runner.session.wait_prompt(1500)
        if runner.session.last_line() != '#':
            raise ValueError('INPUT fixture did not return to ZX-UX shell')
        print('NATIVE INPUT OK: typed letters and ENTER returned to shell')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
