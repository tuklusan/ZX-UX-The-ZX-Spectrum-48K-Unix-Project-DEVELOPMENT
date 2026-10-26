"""Verify native SSX1 BSS reset across three jobs in one ZX-UX session.

This checks the kernel loader, not the still-unverified BASIC compiler.
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

PREFIX = '    section text\n    global start\nstart:\n    ld hl,cell\n'
END = '    ret\n    section bss\ncell: ds 1\n'
WRITER = PREFIX + '    ld (hl),73\n    ld hl,0\n    ld a,1\n    call 0x6003\n' + END
READER = (PREFIX + '    ld a,(hl)\n    or a\n    jr nz,failed\n'
          '    ld hl,0\n    ld a,1\n    call 0x6003\nfailed:\n'
          '    ld hl,11\n    ld a,1\n    call 0x6003\n' + END)
CASES = (('write', WRITER), ('read1', READER), ('read2', READER))


def run(system: Path, work: Path) -> dict:
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('missing native kernel metadata')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('native system differs from frozen release')
    work.mkdir(parents=True, exist_ok=True)
    files = []
    sizes = {}
    for name, listing in CASES:
        object_file = rld.Obj(ras.assemble_text(listing), name + '.sso')
        data, _, _, _, _ = rld.link([object_file], [], stack=384)
        parsed = rld.parse_ssx(data)
        total = len(parsed['image']) + parsed['bss'] + parsed['stack']
        if parsed['bss'] != 1 or parsed['relocs'] != [1] or max(len(data), total) > 12000:
            raise RuntimeError(name + ': bad native BSS layout or memory admission')
        target = work / (name + '.ssx')
        target.write_bytes(data)
        files.append(target)
        sizes[name] = {'file': len(data), 'image': len(parsed['image']),
                       'bss': parsed['bss'], 'stack': parsed['stack'],
                       'total': total, 'sha256': hashlib.sha256(data).hexdigest()}
    options = rvm.Options()
    options.prog = str(files[0])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    baseline = (session.word(0x5c36), session.word(0x5c7b))
    exits = []
    for index, file in enumerate(files):
        job = (runner.fg if index == 0 else
               session.launch(file.read_bytes(), rvm.zxux.program_name(str(file))))
        for _ in range(4200):
            runner.frame()
            if job.ended is not None:
                break
        if (job.started is None or job.ended is None or job.status != 0 or
                session.owns_screen(job.pid) or
                (session.word(0x5c36), session.word(0x5c7b)) != baseline):
            raise RuntimeError(file.stem + ': BSS isolation or shell return failed')
        exits.append({'name': file.stem, 'start': job.started,
                      'end': job.ended, 'status': job.status})
    return {'linked': sizes, 'exits': exits, 'shell_chars': baseline[0],
            'shell_udg': baseline[1]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    ap.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate7-bss')
    args = ap.parse_args()
    print('GATE7_NATIVE_BSS', json.dumps(run(args.system, args.work), sort_keys=True))


if __name__ == '__main__':
    main()
