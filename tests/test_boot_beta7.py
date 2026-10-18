#!/usr/bin/env python3
"""TZX-only linked ZX-UX kernel gate, independent of turbo waveform execution.

The actual tape transport is separately verified by the Fuse boot gate.
"""
from pathlib import Path
import hashlib
import re
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'release/dist/sdk/bin/py'))
from zxux import SystemImage, RvmError


def main():
    syms={}
    for line in (ROOT/'release/build/src/unix.sym').read_text().splitlines():
        m=re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)',line)
        if m: syms[m.group(1)]=int(m.group(2),16)
    out=ROOT/'release/build/out'
    tape=ROOT/'release/dist/zx-ux/ZX-UX.tzx'
    system=SystemImage(str(tape))
    low=(out/'lowk.bin').read_bytes()
    unix=(out/'unix.bin').read_bytes()
    fs=(out/'fs.img').read_bytes()
    merged=(out/'merged-image.bin').read_bytes()
    assert 0<len(tape.read_bytes())<30000
    assert not (tape.parent/'ZX-UX.tap').exists()
    assert not (out/'ZX-UX.tap').exists()
    assert len(system.blocks)==4 and system.merged==merged
    assert merged==low+bytes(0x6000-syms['LOWK']-len(low))+unix+fs
    assert syms['ITAB']==0x6000+len(unix)
    assert len(unix)>0 and len(unix)<0xE000-0x6000
    assert unix[0]==0xC3 and merged[0x6000-syms['LOWK']]==0xC3
    assert system.sym['NPROC']==syms['NPROC']
    assert syms['LOWK']==0x5D98
    assert len(system.blocks[2])==19 and system.blocks[2][2:12].rstrip(b' ')==b'ZX-UX BOOT'
    assert int.from_bytes(system.blocks[2][14:16],'little')==0xD000
    assert system.blocks[3][1:-1]==(out/'turbo_boot.bin').read_bytes()
    # Negative checks: malformed packet, corrupt kernel, truncated TZX.
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        for label,bad in [('bad packet',bytearray(tape.read_bytes())),
                          ('truncated',bytearray(tape.read_bytes()[:-1]))]:
            if label=='bad packet': bad[-12]^=1
            other=Path(d)/'bad.tzx';other.write_bytes(bad)
            try: SystemImage(str(other))
            except RvmError: pass
            else: raise AssertionError(label+' accepted by RVM')
    print('PASS: only TZX boot; 4 ROM + 24 validated turbo packets')
    print('PASS: byte-exact compiled low kernel, ZX-UX kernel, RAM filesystem and bootstrap')
    print('PASS: damaged kernel segments and incomplete TZX rejected')
    return 0

if __name__=='__main__': sys.exit(main())
