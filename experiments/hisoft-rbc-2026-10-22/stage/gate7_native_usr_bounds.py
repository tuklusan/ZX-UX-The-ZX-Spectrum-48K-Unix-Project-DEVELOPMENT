"""Prove the typed string-USR 168-byte POKE guard in the real native kernel.

This checks the shared runtime guard and wrapper, not BASIC frontend typing.
"""
from __future__ import annotations

import argparse
import hashlib
import functools
import subprocess
import tempfile
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

from safe_usr_rt import UDG_POKE_CHECK
from native_error_exit import error_exit_asm
import rld
import rvm

OFFSETS = (-1, 0, 167, 168)
BASES = (0x5000, 0x6000, 0x7000)
UDG_SIZE = 168


def assembler(tool: Path, temporary: Path):
    @functools.lru_cache(maxsize=100)
    def assemble(source: str) -> bytes:
        with tempfile.TemporaryDirectory(dir=temporary) as scratch:
            script = Path(scratch) / 'code.asm'
            output = Path(scratch) / 'code.bin'
            instructions = (line.strip() for line in source.split(';'))
            script.write_text('    org 0\n' + ''.join(
                ('' if line.endswith(':') else '    ') + line + '\n'
                for line in instructions if line))
            result = subprocess.run([str(tool), '--nologo', '--raw=' + str(output),
                                     str(script)], text=True, capture_output=True,
                                    timeout=30)
            if result.returncode or not output.is_file():
                raise RuntimeError('Z80 assembler failed: ' + result.stdout + result.stderr)
            return output.read_bytes()
    return assemble


def build(rbc, assemble, source: str, output: Path):
    code = assemble(source)
    builds = [rbc.HiSoftBuild(code, base, base, 0) for base in BASES]
    payload, _ = rbc.build_ssx(builds, bytes(768), rld, 384,
                               use_rom_font=True)
    parsed = rld.parse_ssx(payload)
    memory = len(parsed['image']) + parsed['bss'] + parsed['stack']
    if max(len(payload), memory) > 12000:
        raise RuntimeError('native default memory limit exceeded')
    output.write_bytes(payload)
    return {'file': len(payload), 'image': len(parsed['image']),
            'bss': parsed['bss'], 'stack': parsed['stack'],
            'total': memory, 'sha256': hashlib.sha256(payload).hexdigest()}


def run(compiler: Path, tool: Path, system: Path, work: Path):
    if not (compiler / 'rbc.py').is_file():
        raise RuntimeError('recovered current RBC adapter missing')
    if not tool.is_file():
        raise RuntimeError('native Z80 assembler missing')
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('native kernel symbols missing')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('native kernel differs from frozen release')
    sys.path.insert(0, str(compiler))
    import rbc

    work.mkdir(parents=True, exist_ok=True)
    asm = assembler(tool, work)
    filenames = {}
    sizes = {}
    pause = 'ld bc,65535; wait_loop:; dec bc; ld a,b; or c; jr nz,wait_loop'
    # sjasmplus interprets numeric JR operands as absolute destinations;
    # the HiSoft emitter uses literal signed relative displacements.
    # Label the same branch targets and assert the exact four JR bytes.
    guard = UDG_POKE_CHECK.replace('jr c,+12', 'jr c,guard_reject')
    guard = guard.replace('jr nz,+8', 'jr nz,guard_reject')
    guard = guard.replace('jr nc,+3', 'jr nc,guard_reject')
    guard = guard.replace('jr +15; ', 'jr guard_pass; guard_reject:; ')
    guard = guard.replace(error_exit_asm(11),
                          error_exit_asm(11) + '; guard_pass:')
    for offset in OFFSETS:
        label = ('minus1' if offset == -1 else str(offset))
        target = work / f'usr-{label}.ssx'
        code = ('ld hl,($5c7b); ld de,' + str(offset & 65535) + '; add hl,de; '
                + guard + '; ld (hl),85; ' + pause + '; ret')
        encoded = asm(code)
        for branch in (bytes((0x38, 12)), bytes((0x20, 8)),
                       bytes((0x30, 3)), bytes((0x18, 15))):
            if branch not in encoded:
                raise RuntimeError('HiSoft guard relative displacement differs')
        sizes[label] = build(rbc, asm, code, target)
        filenames[offset] = target
    observer = work / 'observer.ssx'
    sizes['observer'] = build(rbc, asm, pause + '; ret', observer)

    fresh = rvm.run_kernel(observer, frames=15, system=system, cache=True)
    if fresh.why != 'frames':
        raise RuntimeError('fresh observer did not run')
    ptr = fresh.session.word(0x5c7b)
    baseline_udg = bytes(fresh.session.m.mem[ptr:ptr + UDG_SIZE])
    if len(baseline_udg) != UDG_SIZE:
        raise RuntimeError('incomplete baseline UDG allocation')

    options = rvm.Options()
    options.prog = str(filenames[-1])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    shell_ptrs = (session.word(0x5c36), session.word(0x5c7b))
    rows = []
    for index, offset in enumerate(OFFSETS):
        path = filenames[offset]
        job = (runner.fg if index == 0 else
               session.launch(path.read_bytes(), rvm.zxux.program_name(str(path))))
        active = None
        for _ in range(4200):
            runner.frame()
            if job.started is not None and job.ended is None and active is None:
                if session.m.frame - job.started >= 15:
                    ptr = session.word(0x5c7b)
                    active = bytes(session.m.mem[ptr:ptr + UDG_SIZE])
            if job.ended is not None:
                break
        expected = 0 if 0 <= offset < UDG_SIZE else 11
        if (job.started is None or job.ended is None or job.status != expected or
                session.owns_screen(job.pid)):
            raise RuntimeError('native string-USR bounds exit wrong: ' + repr(
                (offset, job.started, job.ended, job.status)))
        if expected == 0:
            comparison = bytearray(baseline_udg)
            comparison[offset] = 85
            if active != bytes(comparison):
                raise RuntimeError('valid graphics offset changed extra bytes: ' + str(offset))
        if (session.word(0x5c36), session.word(0x5c7b)) != shell_ptrs:
            raise RuntimeError('shell graphics pointers not restored')
        following = session.launch(observer.read_bytes(),
                                   rvm.zxux.program_name(str(observer)))
        reset = None
        for _ in range(4200):
            runner.frame()
            if following.started is not None and following.ended is None and reset is None:
                if session.m.frame - following.started >= 15:
                    ptr = session.word(0x5c7b)
                    reset = bytes(session.m.mem[ptr:ptr + UDG_SIZE])
            if following.ended is not None:
                break
        if (following.started is None or following.ended is None or
                following.status != 0 or reset != baseline_udg or
                session.owns_screen(following.pid)):
            raise RuntimeError('UDG data leaked into next process: ' + repr((offset, following.started, following.ended, following.status, None if reset is None else [(i, baseline_udg[i], reset[i]) for i in range(168) if baseline_udg[i] != reset[i]][:25])))
        rows.append({'offset': offset, 'status': job.status,
                     'modified_byte': offset if expected == 0 else None,
                     'observer_reset_bytes': UDG_SIZE, 'screen_released': True})
    return {'linked': sizes, 'tests': rows,
            'shell_chars': shell_ptrs[0], 'shell_udg': shell_ptrs[1]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', type=Path,
                        default=ROOT / 'build/tmp/rbc-checkpoint-recovered/rbc')
    parser.add_argument('--assembler', type=Path, required=True)
    parser.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate7-usr-bounds')
    args = parser.parse_args()
    print('GATE7_USR_BOUNDS', json.dumps(run(args.compiler.resolve(),
        args.assembler.resolve(), args.system.resolve(), args.work.resolve()),
        sort_keys=True))


if __name__ == '__main__':
    main()
