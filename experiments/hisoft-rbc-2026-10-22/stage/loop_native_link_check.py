"""Fail stage 3 if native linked FOR branches remain unresolved.

This checks actual SSX images, not a Python loop-state model. It does not
claim full Spectrum loop behavior; that requires separate execution tests.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_BRANCHES = {0xC2, 0xC3, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA}


def _unresolved_branch(image):
    return [i for i in range(len(image) - 2)
            if image[i] in _BRANCHES and image[i+1:i+3] == b'\xff\xff']


def verify(root: Path):
    root = root.resolve()
    scratch = root / 'build/tmp/rbc-round2'
    scratch.mkdir(parents=True, exist_ok=True)
    compiler = scratch / 'current/rbc/rbc.py'
    upstream = scratch / 'upstream'
    tape = scratch / 'hisoft48.tap'
    sdk = root / 'src/zx-ux-sdk'
    rom = sdk / 'rom/48.rom'
    if not all(p.exists() for p in (compiler, upstream / 'compiler.py', tape, rom)):
        raise RuntimeError('Native loop fixture dependencies absent')
    cases = {
        'paired': '10 FOR I=1 TO 2\n20 PRINT I\n30 NEXT I\n40 STOP\n',
        'unpaired': '10 FOR I=1 TO 2\n20 PRINT I\n30 STOP\n',
        'assigned': '10 FOR I=1 TO 3\n20 LET I=I+1\n30 GO TO 40\n40 NEXT I\n50 STOP\n',
    }
    env = dict(os.environ, PYTHONPATH=str(upstream))
    sys.path.insert(0, str(sdk))
    import rld
    for name, listing in cases.items():
        source = scratch / ('loop-' + name + '.bas')
        target = scratch / ('loop-' + name + '.ssx')
        source.write_text(listing, encoding='ascii')
        target.unlink(missing_ok=True)
        args = [sys.executable, str(compiler), str(source), '--frontend', str(upstream),
                '--sdk', str(sdk), '--rom', str(rom), '--tape', str(tape), '-o', str(target)]
        r = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True)
        if r.returncode or not target.is_file():
            raise RuntimeError(f'Native {name} loop was not linked: ' + r.stderr + r.stdout)
        raw = target.read_bytes()
        image = rld.parse_ssx(raw)['image']
        unresolved = _unresolved_branch(image)
        if unresolved:
            raise RuntimeError(f'Native {name} FOR/NEXT has unresolved branch at image offset {unresolved[0]}')
    print('RBC FOR/NEXT native branch-link smoke PASS:', len(cases), 'SSX files')


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[3])
