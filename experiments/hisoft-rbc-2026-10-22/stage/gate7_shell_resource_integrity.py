"""Check shell font restoration and the full 168-byte private UDG image.

Link the recovered current RBC adapter's actual SSX wrapper at three bases.
These are native Z80 fixtures, not BASIC gameplay or frontend tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from native_error_exit import error_exit_bytes, UDG_BYTES
import rld
import rvm

FONT_START = 0x3C00
FONT_LENGTH = 768
LIMIT = 12000
BASES = (0x5000, 0x6000, 0x7000)


def build(rbc, work):
    mutation = bytes.fromhex('2a7b5c364921444422365c')
    delay = bytes.fromhex('01ffff0b78b120fb')
    variants = {
        'observe': delay + b'\xc9',
        'return': mutation + delay + b'\xc9',
        'error-11': mutation + delay + error_exit_bytes(11),
        'error-10': mutation + delay + error_exit_bytes(10),
    }
    files, sizes = {}, {}
    for name, code in variants.items():
        builds = [rbc.HiSoftBuild(code, base, base, 0) for base in BASES]
        payload, _ = rbc.build_ssx(builds, bytes(FONT_LENGTH), rld,
                                   384, use_rom_font=True)
        parsed = rld.parse_ssx(payload)
        total = len(parsed['image']) + parsed['bss'] + parsed['stack']
        if max(total, len(payload)) > LIMIT:
            raise RuntimeError(name + ': exceeds 12000-byte admission')
        dest = work / (name + '.ssx')
        dest.write_bytes(payload)
        files[name] = dest
        sizes[name] = {'file': len(payload), 'image': len(parsed['image']),
                       'bss': parsed['bss'], 'stack': parsed['stack'],
                       'total': total, 'sha256': hashlib.sha256(payload).hexdigest()}
    return files, sizes


def resources(session):
    chars = session.word(0x5C36)
    udg = session.word(0x5C7B)
    return {'chars': chars, 'udg': udg,
            'rom_font': bytes(session.m.mem[FONT_START:FONT_START + FONT_LENGTH])}


def run(compiler: Path, system: Path, work: Path):
    if not (compiler / 'rbc.py').is_file():
        raise RuntimeError('reconstructed current RBC compiler is required')
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('missing kernel.json for rebuilt ZX-UX')
    frozen = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
    if system.read_bytes() != frozen.read_bytes():
        raise RuntimeError('kernel does not equal frozen release')
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(compiler))
    import rbc
    files, sizes = build(rbc, work)
    fresh = rvm.run_kernel(files['observe'], frames=15, system=system, cache=True)
    if fresh.why != 'frames':
        raise RuntimeError('fresh observer process did not run for 15 frames')
    fresh_ptr = fresh.session.word(0x5C7B)
    fresh_udg = bytes(fresh.session.m.mem[fresh_ptr:fresh_ptr + UDG_BYTES])
    if len(fresh_udg) != UDG_BYTES:
        raise RuntimeError('fresh active glyph bank incomplete')
    options = rvm.Options()
    options.prog = str(files['return'])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    initial = resources(session)
    rows = []
    observations = []
    for index, (name, expected) in enumerate((('return', 0), ('error-11', 11),
                                               ('error-10', 10), ('return', 0))):
        path = files[name]
        job = (runner.fg if index == 0 else
               session.launch(path.read_bytes(), rvm.zxux.program_name(str(path))))
        observed = None
        for _ in range(4200):
            runner.frame()
            if job.started is not None and job.ended is None and observed is None:
                if session.m.frame - job.started >= 15:
                    pointer = session.word(0x5C7B)
                    observed = {'pointer': pointer, 'first_byte': session.m.mem[pointer]}
            if job.ended is not None:
                break
        row = {'name': name, 'status': job.status, 'started': job.started,
               'ended': job.ended, 'active_udg': observed,
               'screen_released': not session.owns_screen(job.pid)}
        if job.started is None or job.ended is None or job.status != expected:
            raise RuntimeError('process exit failed: ' + repr(row))
        if observed is None or observed['pointer'] == initial['udg'] or observed['first_byte'] != 73:
            raise RuntimeError('active private glyph mutation failed: ' + repr(row))
        # The shell's UDG pointer overlaps volatile kernel workspace: its
        # bytes are not a stable shell-owned glyph resource. Test pointer
        # restoration, intact ROM font, and a fresh process-owned bank instead.
        now = resources(session)
        if (now['chars'], now['udg'], now['rom_font']) != (
                initial['chars'], initial['udg'], initial['rom_font']):
            raise RuntimeError('shell CHARS, UDG pointer or ROM font changed: ' + repr(row))
        if not row['screen_released']:
            raise RuntimeError('screen not released after exit: ' + repr(row))
        rows.append(row)
        probe = files['observe']
        check = session.launch(probe.read_bytes(), rvm.zxux.program_name(str(probe)))
        observed_bank = None
        for _ in range(4200):
            runner.frame()
            if check.started is not None and check.ended is None and observed_bank is None:
                if session.m.frame - check.started >= 15:
                    pointer = session.word(0x5C7B)
                    observed_bank = bytes(session.m.mem[pointer:pointer + UDG_BYTES])
            if check.ended is not None:
                break
        if (check.started is None or check.ended is None or check.status != 0 or
                observed_bank != fresh_udg):
            raise RuntimeError('new process inherited prior UDG contents: ' + repr({
                'status': check.status, 'observed_length':
                len(observed_bank) if observed_bank is not None else None}))
        after = resources(session)
        if (after['chars'], after['udg'], after['rom_font']) != (
                initial['chars'], initial['udg'], initial['rom_font']):
            raise RuntimeError('observer failed to restore shell font or UDG pointer')
        observations.append({'after': name, 'identical_glyph_bytes': UDG_BYTES,
                             'started': check.started, 'ended': check.ended,
                             'status': check.status})
    return {'kernel_sha256': hashlib.sha256(system.read_bytes()).hexdigest(),
            'baseline_chars': initial['chars'], 'baseline_udg': initial['udg'],
            'udg_bytes_checked': len(fresh_udg),
            'rom_font_bytes_checked': len(initial['rom_font']),
            'linked': sizes, 'runs': rows, 'fresh_observers': observations}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', type=Path,
                        default=ROOT / 'build/tmp/rbc-checkpoint-recovered/rbc')
    parser.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate7-resources')
    args = parser.parse_args()
    print('GATE7_SHELL_RESOURCES', json.dumps(run(args.compiler.resolve(),
                                                 args.system.resolve(),
                                                 args.work.resolve()), sort_keys=True))


if __name__ == '__main__':
    main()
