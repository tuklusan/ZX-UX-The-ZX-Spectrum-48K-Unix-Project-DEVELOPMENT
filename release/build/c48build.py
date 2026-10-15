"""Build individually playable C48 tapes from the locally staged SDK."""
from __future__ import annotations
import json
import pathlib
import struct
import sys


def build(stage_sdk: pathlib.Path, programs: pathlib.Path, dest: pathlib.Path):
    sys.path.insert(0, str(stage_sdk))
    import rtap
    from rcc import driver

    runs = json.loads((programs / 'runs.json').read_text())
    ssxdir, tzxdir = dest / 'ssx', dest / 'tzx'
    ssxdir.mkdir(parents=True, exist_ok=True)
    tzxdir.mkdir(parents=True, exist_ok=True)
    choices = {}
    for name, entry in runs.items():
        if ':' in name:
            continue
        path = programs / entry['dir'] / (entry.get('src', name) + '.c')
        if not path.is_file():
            raise RuntimeError('Selected source is missing: ' + str(path))
        choices[name] = (path, [])
    for name, flags in (
        ('hanoi-mt', ['--bytecode', '--stack', '400', '--udgs', '16']),
        ('queens8-mt', ['--bytecode', '--stack', '448']),
        ('mobius-mt', ['--bytecode']),
        ('torus-mt', ['--bytecode']),
    ):
        source = name[:-3]
        choices[name] = (programs / 'demos' / (source + '.c'), flags)
    for name, (source, flags) in sorted(choices.items()):
        ssx = ssxdir / (name + '.ssx')
        if driver.main([str(source), '-o', str(ssx)] + flags):
            raise RuntimeError('Compiler rejected selected program: ' + name)
        data = ssx.read_bytes()
        tape_name = name.replace('-mt', 'mt')
        if len(tape_name) > 10:
            raise RuntimeError('Tape filename exceeds 10-character header: ' + tape_name)
        hdr, code = rtap.records(data, tape_name)
        title = ('ZX-UX C48 ' + name).encode('ascii')
        if len(title) > 255:
            raise RuntimeError('Tape description is too long')
        head = b'ZXTape!\x1a\x01\x14' + bytes((0x30, len(title))) + title
        tape = tzxdir / (name + '.tzx')
        rtap.write(str(tape), head, [(1000, hdr), (2000, code)])
        _, blocks = rtap.tzx_blocks(tape.read_bytes())
        if len(blocks) != 2 or blocks[0][1] != hdr or blocks[1][1] != code:
            raise RuntimeError('Bad individual tape for ' + name)
    expected = set(choices)
    actual_ssx = {p.stem for p in ssxdir.glob('*.ssx')}
    actual_tzx = {p.stem for p in tzxdir.glob('*.tzx')}
    if expected != actual_ssx or expected != actual_tzx:
        raise RuntimeError('Incorrect file set for individual program tapes')
    return len(choices)
