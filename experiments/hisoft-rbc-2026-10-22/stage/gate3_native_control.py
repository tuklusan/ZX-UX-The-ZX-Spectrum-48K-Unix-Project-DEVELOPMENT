"""Exercise computed branches, altered FOR indices, and protected native POKE.

Compile unchanged numbered Spectrum BASIC fixtures with the checked RBC and
execute through the real ZX-UX system tape. Work remains below build/tmp.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
import rld
import rvm

CASES = {
    'goto-variable': ('10 LET A=100\n20 GO TO A\n30 POKE USR "a",1\n40 GO TO 40\n100 POKE USR "a",17\n110 GO TO 110\n', 17, 0),
    'gosub-variable': ('10 LET A=100\n20 GO SUB A\n30 POKE USR "a",27\n40 GO TO 40\n100 RETURN\n', 27, 0),
    'for-index-modified': ('10 LET V=0\n20 FOR I=1 TO 7\n30 LET V=V+1\n40 LET I=I+1\n50 NEXT I\n60 POKE USR "a",V\n70 GO TO 70\n', 4, 0),
    'poke-variable': ('10 LET A=USR "a"+3\n20 POKE A,77\n30 GO TO 30\n', 77, 3),
    'protected-poke': ('10 LET P=24576\n20 POKE P,253\n30 GO TO 30\n', None, None),
}


def run(root: Path, workspace: Path, system: Path) -> dict:
    if not system.with_name('kernel.json').is_file():
        raise ValueError('Native kernel metadata absent')
    if system.read_bytes() != (root / 'dist/zx-ux/tzx/ZX-UX.tzx').read_bytes():
        raise ValueError('Test kernel differs from frozen tape')
    workspace.mkdir(parents=True, exist_ok=True)
    outcomes = {}
    for name, (listing, expected, offset) in CASES.items():
        source = workspace / (name + '.bas')
        binary = workspace / (name + '.ssx')
        source.write_text(listing, encoding='ascii')
        args = [sys.executable, str(root / 'trial-result/rbc/rbc.py'), str(source),
                '--frontend', str(root / 'upstream-pyhsb'),
                '--sdk', str(root / 'src/zx-ux-sdk'),
                '--rom', str(root / 'src/zx-ux-sdk/rom/48.rom'),
                '--tape', str(root / 'trial-result/hisoft48.tap'),
                '--max', '12000', '-o', str(binary)]
        result = subprocess.run(args, cwd=root, text=True, capture_output=True, timeout=110)
        row = {'compile_exit': result.returncode,
               'compiler_stdout': result.stdout[-1200:],
               'compiler_stderr': result.stderr[-1200:]}
        if result.returncode == 0 and binary.is_file():
            payload = binary.read_bytes()
            layout = rld.parse_ssx(payload)
            reserved = len(layout['image']) + layout['bss'] + layout['stack']
            row.update(file_bytes=len(payload), image_bytes=len(layout['image']),
                       bss_bytes=layout['bss'], stack_bytes=layout['stack'],
                       reserved_bytes=reserved,
                       output_sha256=hashlib.sha256(payload).hexdigest())
            if max(reserved, len(payload)) <= 12000:
                try:
                    vm = rvm.run_kernel(binary, frames=470, system=system, cache=True)
                    memory = vm.session.m.mem
                    started = bool(vm.fg and vm.fg.started is not None)
                    row.update(started=started, reason=vm.why,
                               status=vm.fg.status if vm.fg and vm.why == 'exit' else None)
                    if offset is None:
                        row['kernel_code_intact'] = memory[24576] != 253
                        row['pass'] = (started and vm.why == 'exit'
                                       and row['kernel_code_intact'])
                    else:
                        udg = memory[0x5c7b] + 256 * memory[0x5c7c]
                        observed = memory[udg + offset]
                        row.update(observed=observed, expected=expected)
                        row['pass'] = started and vm.why == 'frames' and observed == expected
                except Exception as exc:
                    row['runtime_error'] = f'{type(exc).__name__}: {exc}'
            else:
                row['error'] = 'Native memory budget exceeded'
        outcomes[name] = row
        print('GATE3_NATIVE', name, json.dumps(row), flush=True)
    (workspace / 'gate3-controls.json').write_text(json.dumps(outcomes, indent=2) + '\n')
    if not all(x.get('pass') for x in outcomes.values()):
        raise RuntimeError('One or more native control-flow cases failed')
    return outcomes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, default=ROOT / 'build/tmp/rbc-gate3-native')
    parser.add_argument('--system', type=Path, default=ROOT / 'build/out/ZX-UX.tzx')
    args = parser.parse_args()
    run(ROOT, args.workspace.resolve(), args.system.resolve())


if __name__ == '__main__':
    main()
