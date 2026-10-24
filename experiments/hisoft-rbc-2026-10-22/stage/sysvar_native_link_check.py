"""Stage-2 compiler/linker smoke: real SSX with private FLAGS2/PIP/FRAMES."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


def verify(root: Path):
    root = root.resolve()
    scratch = root / 'build/tmp/rbc-round2'
    scratch.mkdir(parents=True, exist_ok=True)
    basic = scratch / 'sysvars-smoke.bas'
    basic.write_text('10 POKE 23658,9\n20 POKE 23609,111\n'
                     '30 POKE 23672,255: POKE 23673,255: POKE 23674,255\n'
                     '40 PRINT PEEK 23658; PEEK 23609; PEEK 23672\n'
                     '50 PRINT PEEK 23673; PEEK 23674\n')
    compiler = scratch / 'current/rbc/rbc.py'
    upstream = scratch / 'upstream'
    tape = scratch / 'hisoft48.tap'
    rom = root / 'src/zx-ux-sdk/rom/48.rom'
    sdk = root / 'src/zx-ux-sdk'
    if not all(p.exists() for p in (compiler,upstream / 'compiler.py',tape,rom)):
        raise RuntimeError('ZX-UX validation check failed.')
    env = dict(os.environ)
    env['PYTHONPATH'] = str(upstream)
    outputs=[]
    for copy in (1,2):
        target=scratch / f'sysvars-smoke-{copy}.ssx'
        target.unlink(missing_ok=True)
        command=[sys.executable,str(compiler),str(basic),'--frontend',str(upstream),
                 '--sdk',str(sdk),'--rom',str(rom),'--tape',str(tape),
                 '-o',str(target)]
        result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True)
        if result.returncode or not target.is_file():
            raise RuntimeError('native linked system-variable smoke failed: '
                               +result.stderr+result.stdout)
        outputs.append(target.read_bytes())
    sys.path.insert(0,str(sdk))
    import rld
    parsed = rld.parse_ssx(outputs[0])
    if not outputs[0].startswith(b'SSX1') or outputs[0]!=outputs[1]:
        raise RuntimeError('nondeterministic or invalid system-variable SSX output')
    if parsed['bss'] < 8:
        raise RuntimeError('native compiler omitted private system-variable BSS')
    print('RBC system-variable native link PASS:',len(outputs[0]),'SSX bytes,',
          'BSS',parsed['bss'],'SHA-256',hashlib.sha256(outputs[0]).hexdigest())


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[3])
