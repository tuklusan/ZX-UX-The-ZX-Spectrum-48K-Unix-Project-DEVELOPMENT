"""Build individually playable C48 tapes from the locally staged SDK."""
from __future__ import annotations
import pathlib
import sys


def build(stage_sdk: pathlib.Path, programs: pathlib.Path, dest: pathlib.Path):
    sys.path.insert(0, str(stage_sdk))
    import rtap
    from rcc import driver

    ssxdir, tzxdir = dest / 'ssx', dest / 'tzx'
    ssxdir.mkdir(parents=True, exist_ok=True)
    tzxdir.mkdir(parents=True, exist_ok=True)
    # The source tree determines the selection.  Any same-stem assembly
    # companion is discovered and linked by RCC itself.
    def tape_name(p):
        if p.parent.name == 'examples' and p.stem == 'maze':
            return 'maze1982'
        if p.parent.name == 'games' and p.stem == 'maze1982':
            return 'maze1996'  # distinct Mark Green game, not the C48 example
        return p.stem

    choices = {tape_name(p): p for p in programs.rglob('*.c')
               if p.name != 'seckern.c'}
    for name, source in sorted(choices.items()):
        ssx = ssxdir / (name + '.ssx')
        if driver.main([str(source), '-o', str(ssx)]):
            raise RuntimeError('Compiler rejected selected program: ' + name)
        data = ssx.read_bytes()
        tape_name = name
        if len(tape_name) > 10:
            raise RuntimeError('Tape filename exceeds 10-character header: ' + tape_name)
        hdr, code = rtap.records(data, tape_name)
        title = ('ZX-UX C48 ' + name).encode('ascii')
        if len(title) > 255:
            raise RuntimeError('Tape description is too long')
        head = b'ZXTape!\x1a\x01\x14' + bytes((0x30, len(title))) + title
        tape = tzxdir / (name + '.tzx')
        rtap.write(str(tape), head, [(1000, hdr), (2000, code)])
    return len(choices)
