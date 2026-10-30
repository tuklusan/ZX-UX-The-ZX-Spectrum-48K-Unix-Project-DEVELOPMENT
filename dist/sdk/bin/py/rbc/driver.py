"""Native 48K Spectrum BASIC -> ZX-UX SSX1 using checked HiSoft 1.1 sources."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
SDK = HERE.parent


def main(argv=None):
    parser = argparse.ArgumentParser(description='RBC: strict native Spectrum 48K BASIC compiler')
    parser.add_argument('source', type=Path, help='numbered .bas, or .tzx with matching .bas')
    parser.add_argument('-o', '--output', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-S', action='store_true', help='pre-link Z80 assembler source')
    mode.add_argument('-c', action='store_true', help='relocatable ras object')
    parser.add_argument('--max', type=int, default=14000)
    parser.add_argument('--stack', type=int, default=384)
    args = parser.parse_args(argv)
    source = args.source.resolve()
    target = (args.output or source.with_suffix('.s' if args.S else '.sso' if args.c else '.ssx')).resolve()
    if target == source:
        parser.error('cannot overwrite source')
    if not source.is_file():
        parser.error('source does not exist')
    if source.suffix.lower() not in ('.bas', '.tzx'):
        parser.error('requires numbered .bas or original .tzx')
    if args.stack <= 0 or args.max <= 0:
        parser.error('--stack and --max must be positive')
    from .native_rbc_cli import compile_native
    sys.path.insert(0, str(HERE / 'frontend'))
    try:
        with TemporaryDirectory(prefix='rbc-') as tmp:
            inp = source
            if source.suffix.lower() == '.tzx':
                original_bas = source.with_suffix('.bas')
                if not original_bas.is_file():
                    raise ValueError('independent TZX input requires a matching original BAS for token-by-token validation')
                from .dual_source import convert_tzx
                from . import engine
                from . import dual_source
                import source as hisoft_source
                import compiler as hisoft_compiler
                # The canonical frontend is bundled locally and validated by source checks.
                rom = (SDK / 'rom/48.rom').read_bytes()
                kw = hisoft_source.Keywords(rom)
                fp = hisoft_compiler.Compiler(
                    __import__('hbcimage').Image.from_tape(HERE / 'hisoft48.tap'), rom,
                    ramtop=65367).fp
                inp = Path(tmp) / (source.stem + '.bas')
                dual_source.convert_tzx(source, original_bas, inp,
                                        engine, hisoft_source, kw, fp)
            asm, obj, ssx, report = compile_native(
                inp, HERE, HERE / 'frontend', HERE / 'hisoft48.tap',
                SDK / 'rom/48.rom', stack=args.stack, maximum=args.max)
            payload = asm.encode('ascii') if args.S else obj if args.c else ssx
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        print(f'RBC_NATIVE_OK file={report["file"]} image={report["image"]} '
              f'bss={report["bss"]} stack={report["stack"]} '
              f'total={report["total"]} relocs={report["relocations"]}')
        return 0
    except Exception as exc:
        print(f'RBC_NATIVE_BLOCKED {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
