"""Check native BASIC wrapper restores printer and keyboard state on all exits.

Each linked SSX mutates physical ROM printer settings, FLAGS2 and PIP.
This is a low-level native wrapper gate, not BASIC source verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
from native_error_exit import error_exit_bytes
import rld
import rvm

SYSTEM_VARIABLES = (0x5C8D, 0x5C8E, 0x5C8F, 0x5C90, 0x5C6A, 0x5C39)
MUTATIONS = (0x12, 0x34, 0x56, 0x78, 0x88, 0x99)
BASES = (0x5000, 0x6000, 0x7000)
DELAY = bytes.fromhex('01ffff0b78b120fb')


def state(session):
    return bytes(session.m.mem[address] for address in SYSTEM_VARIABLES)


def program(exit_code: bytes) -> bytes:
    code = bytearray()
    for address, value in zip(SYSTEM_VARIABLES, MUTATIONS):
        code += bytes((0x3E, value, 0x32, address & 255, address >> 8))
    return bytes(code) + DELAY + exit_code


def run(compiler: Path, system: Path, work: Path):
    if not (compiler / 'rbc.py').is_file():
        raise RuntimeError('missing rebuilt current RBC compiler')
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('missing native kernel symbols')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('kernel differs from frozen release')
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(compiler))
    import rbc

    variants = {'normal': (b'\xC9', 0),
                'error-11': (error_exit_bytes(11), 11),
                'error-10': (error_exit_bytes(10), 10)}
    files = {}
    dimensions = {}
    for name, (ending, expected) in variants.items():
        body = program(ending)
        builds = [rbc.HiSoftBuild(body, base, base, 0) for base in BASES]
        payload, _ = rbc.build_ssx(builds, bytes(768), rld, 384, use_rom_font=True)
        parsed = rld.parse_ssx(payload)
        total = len(parsed['image']) + parsed['bss'] + parsed['stack']
        if max(total, len(payload)) > 12000:
            raise RuntimeError(name + ': fails default memory admission')
        file = work / (name + '.ssx')
        file.write_bytes(payload)
        files[name] = file
        dimensions[name] = {'file': len(payload), 'image': len(parsed['image']),
                            'bss': parsed['bss'], 'stack': parsed['stack'],
                            'total': total, 'sha256': hashlib.sha256(payload).hexdigest()}

    options = rvm.Options()
    options.prog = str(files['normal'])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    initial = state(session)
    pointers = (session.word(0x5C36), session.word(0x5C7B))
    rows = []
    for i, name in enumerate(('normal', 'error-11', 'error-10', 'normal')):
        file = files[name]
        expected = variants[name][1]
        job = (runner.fg if i == 0 else
               session.launch(file.read_bytes(), rvm.zxux.program_name(str(file))))
        active = None
        for _ in range(4200):
            runner.frame()
            if job.started is not None and job.ended is None and active is None:
                if session.m.frame - job.started >= 15:
                    active = state(session)
            if job.ended is not None:
                break
        row = {'case': name, 'status': job.status,
               'started': job.started, 'ended': job.ended,
               'active': list(active) if active is not None else None,
               'screen_released': not session.owns_screen(job.pid)}
        if job.started is None or job.ended is None or job.status != expected:
            raise RuntimeError('native exit status mismatch: ' + repr(row))
        if active != bytes(MUTATIONS):
            raise RuntimeError('active native settings did not mutate: ' + repr(row))
        if state(session) != initial:
            raise RuntimeError('ROM settings not restored on native exit: ' + repr(row))
        if (session.word(0x5C36), session.word(0x5C7B)) != pointers:
            raise RuntimeError('shell graphics pointers not restored: ' + repr(row))
        if not row['screen_released']:
            raise RuntimeError('screen leaked on native exit: ' + repr(row))
        rows.append(row)
    return {'shell_values': list(initial), 'linked': dimensions,
            'exits': rows, 'restored_bytes': len(initial)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', type=Path,
                        default=ROOT / 'build/tmp/rbc-checkpoint-recovered/rbc')
    parser.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate7-control-restore')
    args = parser.parse_args()
    print('GATE7_NATIVE_CONTROL_RESTORE', json.dumps(
        run(args.compiler.resolve(), args.system.resolve(), args.work.resolve()),
        sort_keys=True))


if __name__ == '__main__':
    main()
