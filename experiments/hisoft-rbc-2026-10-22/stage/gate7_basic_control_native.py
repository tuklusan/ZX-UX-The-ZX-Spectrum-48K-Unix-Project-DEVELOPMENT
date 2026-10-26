"""Compile and execute Spectrum BASIC RUN, GO SUB, STOP and native error probes.

Tests the current RBC and native ZX-UX kernel, not whole-gameplay behavior.
Uses fresh numbered ASCII test sources; original 60-game inputs are untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SDK = ROOT / 'src/zx-ux-sdk'
sys.path.insert(0, str(SDK))
import rld
import rvm

CASES = {
    'stop': ("10 REM : OPEN #\n20 STOP\n", 0, None),
    'gosub': (
        '10 REM : OPEN #\n20 LET A=0\n30 GO SUB 100\n'
        '40 IF A=3 THEN GO TO 200\n50 GO TO 300\n'
        '100 LET A=A+3\n110 RETURN\n'
        '200 POKE 22528,34: PAUSE 30: STOP\n'
        '300 POKE 22528,68: PAUSE 30: STOP\n', 0, 34),
    'wrong-branch': (
        '10 REM : OPEN #\n20 LET A=1\n30 GO SUB 100\n'
        '40 IF A=3 THEN GO TO 200\n50 GO TO 300\n'
        '100 LET A=A+3\n110 RETURN\n'
        '200 POKE 22528,34: PAUSE 30: STOP\n'
        '300 POKE 22528,68: PAUSE 30: STOP\n', 0, 68),
    'run': (
        '10 REM : OPEN #\n20 RUN 100\n'
        '30 POKE 22528,68: PAUSE 30: STOP\n'
        '100 POKE 22528,34: PAUSE 30: STOP\n', 0, 34),
    'protected-poke': (
        '10 REM : OPEN #\n20 LET A=23562\n30 POKE A,77\n', 11, None),
    'val-legal': (
        '10 REM : OPEN #\n20 LET A$="2+3"\n30 LET B=VAL A$\n'
        '40 IF B=5 THEN GO TO 100\n'
        '50 POKE 22528,68: PAUSE 30: STOP\n'
        '100 POKE 22528,34: PAUSE 30: STOP\n', 0, 34),
    'val-ascii-usr': (
        '10 REM : OPEN #\n20 LET A$="USR 32768"\n'
        '30 PRINT VAL A$\n', 10, None),
    'val-token-usr': (
        '10 REM : OPEN #\n20 LET A$=CHR$(192)+" 32768"\n'
        '30 PRINT VAL A$\n', 10, None),
}
SEQUENCE = ('stop', 'gosub', 'wrong-branch', 'run', 'protected-poke',
            'val-legal', 'val-ascii-usr', 'val-token-usr', 'gosub')


def compile_cases(compiler: Path, frontend: Path, tape: Path, rom: Path,
                  work: Path):
    files, dimensions = {}, {}
    for name, (source, _status, _attribute) in CASES.items():
        bas = work / (name + '.bas')
        binary = work / (name + '.ssx')
        bas.write_bytes(source.encode('ascii'))
        command = [sys.executable, str(compiler / 'rbc.py'), str(bas),
                   '--frontend', str(frontend), '--tape', str(tape),
                   '--rom', str(rom), '--sdk', str(SDK),
                   '--max', '12000', '-o', str(binary)]
        completed = subprocess.run(command, text=True, capture_output=True,
                                   timeout=90)
        if completed.returncode or not binary.is_file():
            raise RuntimeError(name + ': compiler failed: ' +
                               completed.stdout + completed.stderr)
        payload = binary.read_bytes()
        parsed = rld.parse_ssx(payload)
        total = len(parsed['image']) + parsed['bss'] + parsed['stack']
        if max(len(payload), total) > 12000:
            raise RuntimeError(name + ': linked image fails 12 KB limit')
        dimensions[name] = {'source_sha256': hashlib.sha256(bas.read_bytes()).hexdigest(),
                            'file': len(payload), 'image': len(parsed['image']),
                            'bss': parsed['bss'], 'stack': parsed['stack'],
                            'total': total, 'ssx_sha256': hashlib.sha256(payload).hexdigest()}
        files[name] = binary
    return files, dimensions


def run(compiler: Path, frontend: Path, tape: Path, rom: Path,
        system: Path, work: Path):
    if not (compiler / 'rbc.py').is_file():
        raise RuntimeError('reconstructed current RBC compiler missing')
    if not (frontend / 'compiler.py').is_file():
        raise RuntimeError('canonical HiSoft frontend missing')
    if not tape.is_file() or not rom.is_file():
        raise RuntimeError('authenticated HiSoft tape and ZX Spectrum ROM required')
    if not system.with_name('kernel.json').is_file():
        raise RuntimeError('rebuilt ZX-UX kernel metadata missing')
    if system.read_bytes() != (ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise RuntimeError('native kernel differs from frozen release')
    work.mkdir(parents=True, exist_ok=True)
    files, dimensions = compile_cases(compiler, frontend, tape, rom, work)

    options = rvm.Options()
    options.prog = str(files[SEQUENCE[0]])
    options.system = str(system)
    options.cache = True
    runner = rvm.Runner(options)
    runner.start()
    session = runner.session
    baseline = (session.word(0x5c36), session.word(0x5c7b))
    baseline_attribute = session.m.mem[22528]
    rows = []
    for index, name in enumerate(SEQUENCE):
        path = files[name]
        expected_status, expected_attribute = CASES[name][1:]
        job = (runner.fg if index == 0 else
               session.launch(path.read_bytes(), rvm.zxux.program_name(str(path))))
        sampled = None
        for _ in range(3000):
            runner.frame()
            if job.started is not None and job.ended is None and sampled is None:
                if session.m.frame - job.started >= 15:
                    sampled = session.m.mem[22528]
            if job.ended is not None:
                break
        row = {'program': name, 'status': job.status, 'started': job.started,
               'ended': job.ended, 'active_attribute': sampled,
               'screen_released': not session.owns_screen(job.pid)}
        if (job.started is None or job.ended is None or
                job.status != expected_status or not row['screen_released']):
            raise RuntimeError(name + ': BASIC process did not finish safely: ' + repr(row))
        if expected_attribute is not None and sampled != expected_attribute:
            raise RuntimeError(name + ': incorrect BASIC flow/POKE: ' + repr(row))
        if (session.word(0x5c36), session.word(0x5c7b)) != baseline:
            raise RuntimeError(name + ': shell CHARS/UDG pointer changed')
        if session.m.mem[22528] != baseline_attribute:
            raise RuntimeError(name + ': shell screen attribute changed')
        rows.append(row)
    return {'linked': dimensions, 'runs': rows,
            'shell_chars': baseline[0], 'shell_udg': baseline[1],
            'shell_attribute': baseline_attribute}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--frontend', type=Path, required=True)
    parser.add_argument('--tape', type=Path, required=True)
    parser.add_argument('--rom', type=Path, default=SDK / 'rom/48.rom')
    parser.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    parser.add_argument('--work', type=Path, default=ROOT / 'build/tmp/rbc-gate7-basic-control')
    args = parser.parse_args()
    print('GATE7_BASIC_CONTROL', json.dumps(run(args.compiler.resolve(),
        args.frontend.resolve(), args.tape.resolve(), args.rom.resolve(),
        args.system.resolve(), args.work.resolve()), sort_keys=True))


if __name__ == '__main__':
    main()
