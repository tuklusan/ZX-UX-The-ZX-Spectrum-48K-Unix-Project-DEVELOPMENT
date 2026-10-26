"""Verify exact upeepz80 on typed full-program assembly and native ras/rld.

This isolated generator proves the optimizer/linker interface. It does not
claim that legacy HiSoft compiler emission has been converted to typed Z80.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
import rvm
from symbolic_z80 import SymbolicProgram

SOURCE_BLOBS = {
    '__init__.py': 'd5bf9e1ca2f80d671c09231520af1470cb7a185e',
    'peephole.py': '067ac45ed935fbe90f9e24a864cdf2eca163cc4c',
    'z80.py': '550b14e167a4a265aada5901d86e506225a9a1b9',
}
REVISION = 'a48d725704b132c3ff23ac77232a3a412b56b15f'


def assemble_fixture():
    program = SymbolicProgram()
    program.label('start', entry=True)
    for ins in ('ld a,0', 'or a', 'jp nz,bad', 'ld hl,0',
                'jp done'):
        program.instruction(ins)
    program.label('bad')
    program.instruction('ld hl,11')
    program.label('done')
    for ins in ('ld a,1', 'call 0x6003', 'ret'):
        program.instruction(ins)
    program.section('data')
    program.label('resource')
    program.binary(bytes((0xc3, 0x18, 0x00, 0x76, 0x21)))
    program.reference('done')
    program.section('bss')
    program.label('scratch')
    program.reserve(16)
    return program


def run(upstream: Path, system: Path, work: Path):
    upstream = upstream.resolve()
    folder = upstream / 'upeepz80'
    for name, expected in SOURCE_BLOBS.items():
        path = folder / name
        if not path.is_file():
            raise ValueError('missing exact upeepz80 source: ' + name)
        actual = subprocess.run(['git', 'hash-object', str(path)],
                                text=True, check=True, capture_output=True).stdout.strip()
        if actual != expected:
            raise ValueError(name + ': source revision blob mismatch')
    if not system.with_name('kernel.json').is_file():
        raise ValueError('rebuilt ZX-UX kernel metadata required')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise ValueError('rebuilt kernel differs from frozen tape')
    sys.path.insert(0, str(upstream))
    from upeepz80 import PeepholeOptimizer
    program = assemble_fixture()
    plain, plain_sizes = program.optimize(lambda source: source, ras, rld)
    optimizer = PeepholeOptimizer()
    better, better_sizes = program.optimize(optimizer.optimize, ras, rld)
    if better_sizes['saved_file_bytes'] < 1 or better_sizes['saved_memory_bytes'] < 1:
        raise ValueError('whole-program optimizer produced no proven reduction')
    actual = rld.parse_ssx(better)
    original = rld.parse_ssx(plain)
    if actual['bss'] != original['bss'] or actual['stack'] != original['stack']:
        raise RuntimeError('linked storage was modified')
    if actual['image'][-7:-2] != original['image'][-7:-2] or actual['image'][-7:-2] != bytes((0xc3, 0x18, 0, 0x76, 0x21)):
        raise RuntimeError('protected binary source bytes changed')
    work.mkdir(parents=True, exist_ok=True)
    binaries = []
    for label, payload in (('plain', plain), ('optimized', better)):
        path = work / (label + '.ssx')
        path.write_bytes(payload)
        binaries.append((label, path))
    options = rvm.Options()
    options.prog = str(binaries[0][1])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    resources = (session.word(0x5c36), session.word(0x5c7b))
    outcomes = []
    for index, (label, path) in enumerate(binaries):
        job = (runner.fg if index == 0 else session.launch(
            path.read_bytes(), rvm.zxux.program_name(str(path))))
        for _ in range(4200):
            runner.frame()
            if job.ended is not None:
                break
        if (job.started is None or job.ended is None or job.status != 0 or
                session.owns_screen(job.pid) or
                (session.word(0x5c36), session.word(0x5c7b)) != resources):
            raise RuntimeError('native ' + label + ' semantics or shell return mismatch')
        outcomes.append({'name': label, 'exit': job.status,
                         'start': job.started, 'end': job.ended,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'optimizer_revision': REVISION, 'plain': plain_sizes,
            'optimized': better_sizes, 'optimizations': optimizer.stats,
            'native_exits': outcomes, 'protected_resource_bytes': 5,
            'hisoft_whole_program_integrated': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--optimizer-source', type=Path, required=True)
    parser.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate8-optimizer-probe')
    args = parser.parse_args()
    print('GATE8_VERIFIED_NATIVE', json.dumps(run(args.optimizer_source,
          args.system.resolve(), args.work.resolve()), sort_keys=True))


if __name__ == '__main__':
    main()
