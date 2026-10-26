"""Check the production UDG cleanup-pointer exit protocol in the native kernel.

The fixture supplies its own cleanup routine; it does not certify the RBC
compiler's complete SSX wrapper or the original BASIC programs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from native_error_exit import UDG_BYTES, error_exit_asm, error_exit_bytes
import ras
import rld
import rvm

STATUSES = (0, 10, 11)


def build(status: int):
    # Assert the text and byte emitter forms produce identical Z80 instructions.
    fragment = ''.join('    ' + ins.strip() + '\n'
                       for ins in error_exit_asm(status).split(';'))
    fragment_obj = rld.Obj(ras.assemble_text('    section text\n' + fragment),
                           'exit-fragment.sso')
    if bytes(fragment_obj.secs[0][2]) != error_exit_bytes(status):
        raise RuntimeError('native error emitter encodings differ')

    # A relocated UDG bank is followed by its relocated cleanup address.
    # The fixture changes CHARS and UDG, then jumps through the production
    # error exit instructions. The cleanup routine restores both globals.
    code = ','.join(map(str, error_exit_bytes(status)))
    listing = f'''    section text
    global start
start:
    ld hl,(0x5c7b)
    ld (shell_udg),hl
    ld hl,(0x5c36)
    ld (shell_chars),hl
    ld hl,udg_image
    ld (0x5c7b),hl
    ld hl,0x4444
    ld (0x5c36),hl
    ld hl,udg_image
    ld (hl),73
    jp raise_error
cleanup:
    push de
    ld hl,(shell_udg)
    ld (0x5c7b),hl
    ld hl,(shell_chars)
    ld (0x5c36),hl
    ld hl,0
    ld a,39
    call 0x6003
    pop hl
    ld a,1
    call 0x6003
    ret
raise_error:
    db {code}
    section data
udg_image:
    db {','.join('0' for _ in range(UDG_BYTES))}
    dw cleanup
shell_udg: dw 0
shell_chars: dw 0
'''
    obj = rld.Obj(ras.assemble_text(listing), f'exit-{status}.sso')
    data, _, _, _, _ = rld.link([obj], [], stack=384)
    layout = rld.parse_ssx(data)
    total = len(layout['image']) + layout['bss'] + layout['stack']
    if max(len(data), total) > 12000:
        raise RuntimeError('default 12000-byte admission failed')
    return data, {'file': len(data), 'image': len(layout['image']),
                  'bss': layout['bss'], 'stack': layout['stack'],
                  'total': total, 'sha256': hashlib.sha256(data).hexdigest()}


def run(system: Path, work: Path):
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('native kernel metadata absent')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('native kernel differs from frozen tape')
    work.mkdir(parents=True, exist_ok=True)
    files, sizes = {}, {}
    for status in STATUSES:
        payload, sizes[status] = build(status)
        target = work / f'exit-{status}.ssx'
        target.write_bytes(payload)
        files[status] = target

    options = rvm.Options()
    options.prog = str(files[0])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    baseline = (session.word(0x5c7b), session.word(0x5c36))
    protected_byte = session.m.mem[0x5c0a]
    rows = []
    for index, status in enumerate((0, 11, 10, 11)):
        source = files[status]
        job = (runner.fg if index == 0 else
               session.launch(source.read_bytes(), rvm.zxux.program_name(str(source))))
        for _ in range(4200):
            runner.frame()
            if job.ended is not None:
                break
        row = {'status': job.status, 'started': job.started, 'ended': job.ended,
               'udg': session.word(0x5c7b), 'chars': session.word(0x5c36),
               'screen_released': not session.owns_screen(job.pid)}
        if (job.started is None or job.ended is None or job.status != status or
                (row['udg'], row['chars']) != baseline or
                not row['screen_released'] or session.m.mem[0x5c0a] != protected_byte):
            raise RuntimeError(f'native cleanup-pointer exit {status} failed: {row}')
        rows.append(row)
    return {'linked': sizes, 'runs': rows,
            'shell_udg': baseline[0], 'shell_chars': baseline[1],
            'protected_memory_unchanged': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--system', type=Path,
                        default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--work', type=Path,
                        default=ROOT / 'build/tmp/rbc-gate7-exit-bridge')
    args = parser.parse_args()
    print('GATE7_NATIVE_ERROR_BRIDGE', json.dumps(run(args.system, args.work),
                                                    sort_keys=True))


if __name__ == '__main__':
    main()
