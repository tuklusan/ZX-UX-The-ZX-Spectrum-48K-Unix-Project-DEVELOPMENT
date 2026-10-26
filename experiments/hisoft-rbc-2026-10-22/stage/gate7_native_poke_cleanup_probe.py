"""Prove native guarded POKE returns through SSX cleanup on the real kernel.

The HiSoft runtime emitter is assembled from source at three load addresses.
The original BASIC frontend and tape are needed for separate source gates.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

from native_sysvars_rt import BSS_BYTES, _native_poke
import rld
import rvm


def assembler(tool: Path, temporary: Path):
    """Assemble the HiSoft runtime Z80 instructions externally."""
    @functools.lru_cache(maxsize=400)
    def assemble(source: str):
        lines = source.replace(';', '\n').splitlines()
        with tempfile.TemporaryDirectory(dir=temporary) as scratch:
            script = Path(scratch) / 'code.asm'
            binary = Path(scratch) / 'code.bin'
            script.write_text('    org 0\n' + ''.join(
                '    ' + line.strip() + '\n' for line in lines if line.strip()))
            result = subprocess.run([str(tool), '--nologo',
                                     '--raw=' + str(binary), str(script)],
                                    text=True, capture_output=True, timeout=30)
            if result.returncode or not binary.is_file():
                raise RuntimeError('Z80 assembler rejected runtime source: ' +
                                   result.stdout + result.stderr)
            return binary.read_bytes()
    return assemble


def native_poke_build(rbc, assemble, base: int):
    # Mutate private UDG and physical CHARS, then attempt a protected POKE
    # into unowned Spectrum system RAM via the actual guarded runtime.
    lead = bytearray(bytes.fromhex(
        '2a7b5c3649'       # LD HL,(UDG); LD (HL),73
        '21444422365c'     # LD HL,4444; LD (CHARS),HL
        '210a5c1e4d'       # LD HL,5C0A; LD E,77
        'cd0000c9'))      # CALL native POKE; RET (unreachable)
    run_offset = len(lead)
    initial = _native_poke(assemble, 0, base, 0, entry=run_offset)
    bss_start = run_offset + len(initial)
    runtime = _native_poke(assemble, bss_start, base,
                           bss_start + BSS_BYTES, entry=run_offset)
    if len(runtime) != len(initial):
        raise RuntimeError('native POKE changed instruction boundaries')
    lead[-3:-1] = (base + run_offset).to_bytes(2, 'little')
    return rbc.HiSoftBuild(bytes(lead) + runtime, base, base, BSS_BYTES)


def link(rbc, builds, work: Path, name: str):
    data, _ = rbc.build_ssx(builds, bytes(768), rld, 384, use_rom_font=True)
    parsed = rld.parse_ssx(data)
    total = len(parsed['image']) + parsed['bss'] + parsed['stack']
    if max(total, len(data)) > 12000:
        raise RuntimeError(name + ': default 12000-byte admission failed')
    path = work / (name + '.ssx')
    path.write_bytes(data)
    return path, {'file': len(data), 'image':len(parsed['image']),
                  'bss':parsed['bss'], 'stack':parsed['stack'], 'total':total,
                  'sha256':hashlib.sha256(data).hexdigest()}


def run(compiler: Path, tool: Path, system: Path, work: Path):
    if not (compiler / 'rbc.py').is_file():
        raise RuntimeError('prepared RBC checkpoint missing')
    if not tool.is_file():
        raise RuntimeError('Z80 assembler missing')
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('native kernel symbols missing')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('native kernel differs from frozen release')
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(compiler))
    import rbc

    asm = assembler(tool, work)
    bases = (0x5000, 0x6000, 0x7000)
    protected, sizes = link(rbc, [native_poke_build(rbc, asm, base)
                                  for base in bases], work, 'protected-poke')
    # Fresh-process source-independent reference, never assume UDG is zero.
    pause = bytes.fromhex('01ffff0b78b120fbc9')
    after, after_sizes = link(rbc, [rbc.HiSoftBuild(pause, b, b, 0)
                                    for b in bases], work, 'after-error')
    fresh = rvm.run_kernel(after, frames=15, system=system, cache=True)
    if fresh.why != 'frames':
        raise RuntimeError('independent graphics baseline did not run')
    fresh_byte = fresh.session.m.mem[fresh.session.word(0x5c7b)]

    options = rvm.Options()
    options.prog, options.system, options.cache = str(protected), str(system), True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    chars = session.word(0x5c36)
    udg = session.word(0x5c7b)
    original_target = session.m.mem[0x5c0a]
    job = runner.fg
    for _ in range(4200):
        runner.frame()
        if job.ended is not None:
            break
    if job.started is None or job.ended is None or job.status != 11:
        raise RuntimeError('native guarded POKE failed to exit with status 11')
    if (session.word(0x5c36) != chars or session.word(0x5c7b) != udg or
            session.m.mem[0x5c0a] != original_target or session.owns_screen(job.pid)):
        raise RuntimeError('protected POKE changed kernel memory or shell graphics')

    following = session.launch(after.read_bytes(), rvm.zxux.program_name(str(after)))
    observed = None
    for _ in range(4200):
        runner.frame()
        if following.started is not None and following.ended is None:
            if session.m.frame - following.started >= 15 and observed is None:
                observed = session.m.mem[session.word(0x5c7b)]
        if following.ended is not None:
            break
    if (following.started is None or following.ended is None or
            following.status != 0 or observed != fresh_byte or
            session.word(0x5c36) != chars or session.word(0x5c7b) != udg or
            session.owns_screen(following.pid)):
        raise RuntimeError('later native process inherited graphics or did not exit')
    return {'protected_poke_status':job.status,'following_status':following.status,
            'shell_chars':chars,'shell_udg':udg,'reference_udg_byte':fresh_byte,
            'following_udg_byte':observed,'protected_memory_unchanged':True,
            'screen_released':True,'protected':sizes,'following':after_sizes}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--compiler', type=Path, required=True)
    p.add_argument('--assembler', type=Path, required=True)
    p.add_argument('--system', type=Path, default=ROOT/'build/out/ZX-UX.tzx')
    p.add_argument('--work', type=Path, default=ROOT/'build/tmp/rbc-gate7-native-poke')
    args = p.parse_args()
    result = run(args.compiler.resolve(),args.assembler.resolve(),
                 args.system.resolve(),args.work.resolve())
    print('GATE7_NATIVE_POKE', json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
