"""Build individually playable C48 tapes from the locally staged SDK."""
from __future__ import annotations
import pathlib
import sys
import tempfile


def build(stage_sdk: pathlib.Path, programs: pathlib.Path, dest: pathlib.Path):
    sys.path.insert(0, str(stage_sdk))
    import rtap
    import ras
    import rld
    from rcc import driver

    ssxdir, tzxdir = dest / 'ssx', dest / 'tzx'
    ssxdir.mkdir(parents=True, exist_ok=True)
    tzxdir.mkdir(parents=True, exist_ok=True)
    # Source tree determines the selection; two intentional exceptions below.
    def tape_name(p):
        if p.parent.name == 'examples' and p.stem == 'maze':
            return 'maze1982'
        if p.parent.name == 'games' and p.stem == 'maze1982':
            return 'maze1996'  # distinct Mark Green game, not the C48 example
        return p.stem

    choices = {tape_name(p): (p, []) for p in programs.rglob('*.c')
               if p.name != 'seckern.c'}
    # The regular program names are also the memory-fitted background jobs.
    # Do not ship separate -mt binaries or tapes for the same C48 source.
    for name, flags in (
        ('hanoi', ['--fit', '--stack', '400', '--udgs', '16']),
        ('queens8', ['--fit', '--stack', '448', '--udgs', '32']),
        ('mobius', ['--bytecode']),
        ('torus', ['--bytecode']),
    ):
        choices[name] = (programs / 'demos' / (name + '.c'), flags)
    # Mixed-language applications supply only application-specific Z80 routines.
    # These stay out of the generic libc48.ssa and link with the C48 object.
    mixed = {'ball': ('demos', 384, {}),
             'invaders': ('games', 800, {'udgs': 32})}
    library = stage_sdk / 'lib/libc48.ssa'
    archives = [rld.read_archive(library.read_bytes(), str(library))]
    for name, (source, flags) in sorted(choices.items()):
        ssx = ssxdir / (name + '.ssx')
        if name in mixed:
            category, stack, opts = mixed[name]
            asm_source = programs / category / (name + '.asm')
            if source != programs / category / (name + '.c') or not asm_source.is_file():
                raise RuntimeError('Missing matching mixed-language source: ' + name)
            with tempfile.TemporaryDirectory(prefix=name + '-', dir=str(stage_sdk.parent)) as tmp:
                temp = pathlib.Path(tmp)
                c_text, _, _ = driver.compile_to_asm(str(source), opts)
                c_sso = temp / (name + '-c.sso')
                asm_sso = temp / (name + '-asm.sso')
                c_sso.write_bytes(ras.assemble_text(c_text, name + '-c.s'))
                asm_sso.write_bytes(ras.assemble_text(asm_source.read_text(), name + '-asm.s'))
                objects = [rld.Obj(c_sso.read_bytes(), c_sso.name),
                           rld.Obj(asm_sso.read_bytes(), asm_sso.name)]
                linked, _, _, _, _ = rld.link(objects, archives, 'start', stack, 0)
                header = rld.parse_ssx(linked)
                need = max(len(header['image']) + header['bss'] + header['stack'], len(linked))
                if need > driver.ZXUX_MAX:
                    raise RuntimeError('%s uses %d bytes (limit %d)' %
                                       (name, need, driver.ZXUX_MAX))
                ssx.write_bytes(linked)
        elif driver.main([str(source), '-o', str(ssx)] + flags):
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
