"""Legacy BASIC-to-C48 hand-port builder. No arbitrary BASIC translation."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

PORTS = Path(__file__).resolve().parent / 'ports'


def available():
    root = PORTS / '60-programs'
    return sorted(path.name for path in root.iterdir() if path.is_dir()) if root.is_dir() else []


def build(source: Path, common: Path, output: Path):
    """Compile one existing C48 hand port; emit the SSX and its TZX tape."""
    from rcc import driver as rcc
    import rld
    import rtap

    source = source.resolve()
    common = common.resolve()
    if source.suffix.lower() != '.c' or not source.is_file():
        raise ValueError('existing hand-ported .c source required')
    stem = source.stem
    if not (1 <= len(stem.encode('ascii')) <= 10):
        raise ValueError('cassette name must be 1..10 ASCII characters')
    for name in ('c48lib.h', 'c48lib.asm', 'c48lib-font.asm'):
        if not (common / name).is_file():
            raise ValueError('missing shared C48 support: ' + name)
    if not output.is_dir():
        raise ValueError('output directory does not exist: ' + str(output))
    # The original sources include ../../c48lib/c48lib.h. Preserve that
    # layout inside a disposable compiler workspace, never touching inputs.
    with TemporaryDirectory(prefix='rb2ct-') as temp:
        root = Path(temp)
        work = root / 'game' / 'C48'
        work.mkdir(parents=True)
        tmp_common = root / 'c48lib'
        tmp_common.mkdir()
        for file in common.iterdir():
            if file.is_file():
                shutil.copyfile(file, tmp_common / file.name)
        for file in source.parent.glob('*.h'):
            shutil.copyfile(file, work / file.name)
        c48 = work / source.name
        shutil.copyfile(source, c48)
        glyphs = source.with_name(stem + '-glyphs.asm')
        parts = [common / 'c48lib.asm', common / 'c48lib-font.asm']
        if glyphs.is_file():
            parts.append(glyphs)
        text = b'; Generated only for this build.\n' + b'\n'.join(
            part.read_bytes().rstrip(b'\r\n') for part in parts)
        if not glyphs.is_file():
            text += b'\nsection data\nc48_game_glyphs:\n    ds 256\n'
        (work / (stem + '.asm')).write_bytes(text)
        binary = work / (stem + '.ssx')
        if rcc.main([str(c48), '-o', str(binary)]):
            raise RuntimeError(stem + ': RCC compilation failed')
        ssx = binary.read_bytes()
        rld.parse_ssx(ssx)
        label = stem
        header, data = rtap.records(ssx, label)
        title = ('ZX-UX RB2CT ' + stem).encode('ascii')
        tzx_head = b'ZXTape!\x1a\x01\x14' + bytes((0x30, len(title))) + title
        tape = work / (stem + '.tzx')
        rtap.write(str(tape), tzx_head, [(1000, header), (2000, data)])
        _, blocks = rtap.tzx_blocks(tape.read_bytes())
        if len(blocks) != 2 or blocks[0][1] != header or blocks[1][1] != data:
            raise RuntimeError(stem + ': cassette verification failed')
        shutil.copyfile(binary, output / binary.name)
        shutil.copyfile(tape, output / tape.name)
    return output / (stem + '.ssx'), output / (stem + '.tzx')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('program', nargs='?', help='bundled hand port name or existing C48 .c file')
    parser.add_argument('-o', '--output-dir', type=Path, default=Path.cwd())
    parser.add_argument('--common', type=Path, help='C48 support directory for external .c files')
    parser.add_argument('--list', action='store_true', help='list available historical hand ports')
    args = parser.parse_args(argv)
    if args.list:
        for name in available():
            print(name)
        return 0
    if not args.program:
        parser.error('existing C48 source or historical hand-port name required')
    try:
        if args.program.endswith('.c'):
            source = Path(args.program)
            common = args.common or source.resolve().parent.parent.parent / 'c48lib'
        else:
            if args.program not in available():
                raise ValueError('no historical C48 hand port: ' + args.program)
            folder = PORTS / '60-programs' / args.program / 'C48'
            files = sorted(folder.glob('*.c'))
            if len(files) != 1:
                raise ValueError('expected one C48 source for ' + args.program)
            source, common = files[0], args.common or PORTS / 'c48lib'
        ssx, tzx = build(source, common, args.output_dir.resolve())
        print(ssx)
        print(tzx)
        return 0
    except (OSError, ValueError, RuntimeError, UnicodeError) as exc:
        print('rb2ct: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
