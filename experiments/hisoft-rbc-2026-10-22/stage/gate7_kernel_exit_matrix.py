"""Exercise native ZX-UX process exits through linked SSO1/SSX1 programs.

This is a kernel baseline, not a substitute for BASIC compiler exit tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import ras
import rld
import rvm

STATUSES = (0, 9, 11)
LIMIT = 12000


def build(status: int) -> tuple[bytes, dict]:
    if status not in STATUSES:
        raise ValueError('unsupported exit probe status')
    listing = ('    section text\n    global start\nstart:\n'
               f'    ld hl,{status}\n    ld a,1\n    call 0x6003\n    ret\n')
    object_file = rld.Obj(ras.assemble_text(listing), f'exit-{status}.sso')
    binary, _, _, _, _ = rld.link([object_file], [], stack=384)
    parsed = rld.parse_ssx(binary)
    if parsed['entry'] != 0:
        raise RuntimeError('unexpected linked entry')
    total = len(parsed['image']) + parsed['bss'] + parsed['stack']
    if max(total, len(binary)) > LIMIT:
        raise RuntimeError('native link exceeds default 12000-byte limit')
    return binary, {'file': len(binary), 'image': len(parsed['image']),
                    'bss': parsed['bss'], 'stack': parsed['stack'],
                    'total': total, 'sha256': hashlib.sha256(binary).hexdigest()}


def run(system: Path, work: Path) -> dict:
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('missing rebuilt native kernel metadata')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('rebuilt kernel differs from frozen release')
    work.mkdir(parents=True, exist_ok=True)
    files = {}
    sizes = {}
    for status in STATUSES:
        data, dimensions = build(status)
        file = work / f'exit-{status}.ssx'
        file.write_bytes(data)
        files[status] = file
        sizes[status] = dimensions

    options = rvm.Options()
    options.prog = str(files[0])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    shell_chars = session.word(0x5c36)
    shell_udg = session.word(0x5c7b)
    protected_byte = session.m.mem[0x5c0a]
    results = []
    for index, status in enumerate(STATUSES):
        file = files[status]
        job = (runner.fg if index == 0 else
               session.launch(file.read_bytes(), rvm.zxux.program_name(str(file))))
        for _ in range(4200):
            runner.frame()
            if job.ended is not None:
                break
        observed = {'status': job.status, 'started': job.started,
                    'ended': job.ended,
                    'screen_released': not session.owns_screen(job.pid),
                    'chars': session.word(0x5c36),
                    'udg': session.word(0x5c7b)}
        if (job.started is None or job.ended is None or job.status != status or
                not observed['screen_released']):
            raise RuntimeError(f'linked native exit {status} failed: {observed}')
        if (observed['chars'] != shell_chars or observed['udg'] != shell_udg or
                session.m.mem[0x5c0a] != protected_byte):
            raise RuntimeError(f'linked native exit {status} altered shell state: {observed}')
        results.append(observed)
    return {'kernel_sha256': hashlib.sha256(system.read_bytes()).hexdigest(),
            'shell_chars': shell_chars, 'shell_udg': shell_udg,
            'linked': sizes, 'exits': results}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    ap.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate7-exits')
    args = ap.parse_args()
    print('GATE7_NATIVE_EXIT_MATRIX', json.dumps(run(args.system, args.work), sort_keys=True))


if __name__ == '__main__':
    main()
