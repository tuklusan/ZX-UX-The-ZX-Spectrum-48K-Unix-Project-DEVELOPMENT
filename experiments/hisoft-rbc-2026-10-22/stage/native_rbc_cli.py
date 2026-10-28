#!/usr/bin/env python3
"""Strict no-optimizer RBC: independently checked HiSoft source -> ras -> rld.

Only original, numbered 48K BASIC is accepted here. The existing HiSoft
compiler must be reproducibly rebuilt from checked Git sources first.
Unsupported cases fail closed. Game behavior needs separate testing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
SDK = ROOT / 'src/zx-ux-sdk'
sys.path[:0] = [str(STAGE), str(SDK)]
import rld
from gate8_full_source_audit import run as audit_original_source
from native_wrapper_source import assemble_link


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _check_equal(native: bytes, reference: bytes) -> None:
    if native == reference:
        return
    first = next((i for i, (a, b) in enumerate(zip(native, reference))
                  if a != b), min(len(native), len(reference)))
    raise ValueError('native ras/rld output differs from the three-base '
                     'HiSoft reference at file offset '
                     f'{first} (native={len(native)}, reference={len(reference)})')


def compile_native(source: Path, checkpoint: Path, frontend: Path,
                   tape: Path, rom: Path, *,
                   stack: int = 384, maximum: int = 14000,
                   use_fit: bool = True) -> tuple[str, bytes, bytes, dict]:
    """Compile from independent source events; never re-encode a linked SSX."""
    if not (source.is_file() and source.suffix.lower() == '.bas'):
        raise ValueError('requires original numbered ASCII .bas source')
    if not all(p.is_file() for p in (checkpoint / 'rbc.py',
                                    checkpoint / 'font32.bin',
                                    frontend / 'compiler.py', tape, rom)):
        raise ValueError('verified HiSoft compiler, frontend, tape and ROM required')
    if type(maximum) is not int or maximum < 0 or type(stack) is not int or stack < 1:
        raise ValueError('invalid --max or --stack')
    if os.environ.get('RBC_G8_OPTIMIZER'):
        raise ValueError('optimizer injection is forbidden in native RBC')
    sys.path.insert(0, str(checkpoint.resolve()))
    import rbc
    font = (checkpoint / 'font32.bin').read_bytes()
    builds, meta = rbc._compile_three(source, frontend, tape, rom,
                                      65367, [], 'strict', False, 1)
    if meta.get('budgeted_numeric_units'):
        raise ValueError('dynamic DIM budget has no three-base source witness yet')
    legacy, _ = rbc.build_ssx(builds, font, rld, stack, use_rom_font=False)
    fitted = (use_fit and maximum and
              max(len(legacy),
                  len(rld.parse_ssx(legacy)['image']) + builds[0].bss + stack) > maximum and
              not meta.get('private_font_requested', False))
    if fitted:
        legacy, _ = rbc.build_ssx(builds, font, rld, stack,
                                      use_rom_font=True)
    source_candidates = []
    proof = audit_original_source(source, checkpoint, frontend, tape, rom,
                                  source_sink=source_candidates.append,
                                  max_bytes=maximum)
    native_proof = proof['native_whole_source_baseline']
    if (len(source_candidates) != 1 or
            not native_proof.get('native_whole_source_baseline_linked') or
            not native_proof.get('native_image_byte_exact') or
            not native_proof.get('all_source_relocations_verified') or
            not proof['native_runtime_region'].get('native_region_verified')):
        raise ValueError('original typed three-base HiSoft source unresolved: ' +
                         str(native_proof.get('blocker', 'missing native witness')))
    sites = rbc._reloc_sites(builds)
    p = builds[0]
    saved_stack = p.base + len(p.code) + p.bss - 2
    restart_slot = p.bss >= 2 and any(
        offset >= 2 and p.code[offset-2:offset] == b'\xed\x7b' and
        int.from_bytes(p.code[offset:offset+2], 'little') == saved_stack
        for offset in sites)
    source_text, obj, native_ssx = assemble_link(
        source_candidates[0], font, use_rom_font=fitted,
        restart_slot=restart_slot, stack=stack)
    # The original wrapper is a *comparison input only*. Its emitted bytes
    # never feed the assembler, linker, returned output, or source generator.
    _check_equal(native_ssx, legacy)
    image = rld.parse_ssx(native_ssx)
    total = len(image['image']) + image['bss'] + image['stack']
    if maximum and max(total, len(native_ssx)) > maximum:
        raise ValueError(f'native memory limit exceeded: file={len(native_ssx)}, '
                         f'image={len(image["image"])}, bss={image["bss"]}, '
                         f'stack={stack}, total={total}, max={maximum}')
    report = {
        'source_sha256': _sha(source.read_bytes()),
        'source': str(source),
        'native_assembly_sha256': _sha(source_text.encode('ascii')),
        'native_object_sha256': _sha(obj),
        'native_ssx_sha256': _sha(native_ssx),
        'file': len(native_ssx), 'image': len(image['image']),
        'bss': image['bss'], 'stack': stack, 'total': total,
        'memory_limit': maximum, 'relocations': len(image['relocs']),
        'native_three_base_source_verified': True,
        'native_and_legacy_ssx_byte_identical': True,
        'native_linker': 'ras/rld',
        'rom_font_used': fitted,
        'optimizer_used': False,
        'loader_execution_tested': False,
        'native_gameplay_tested': False,
    }
    return source_text, obj, native_ssx, report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--compiler', required=True, type=Path,
                   help='checked, recovered RBC directory containing rbc.py')
    p.add_argument('--frontend', required=True, type=Path)
    p.add_argument('--tape', required=True, type=Path)
    p.add_argument('--rom', type=Path, default=SDK / 'rom/48.rom')
    p.add_argument('-o', '--output', type=Path, required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('-S', action='store_true', help='write true pre-link .s')
    mode.add_argument('-c', action='store_true', help='write real ras .sso')
    p.add_argument('--max', type=int, default=14000)
    p.add_argument('--stack', type=int, default=384)
    p.add_argument('--no-fit', action='store_true')
    p.add_argument('--report', type=Path)
    a = p.parse_args(argv)
    try:
        text, obj, ssx, report = compile_native(
            a.source.resolve(), a.compiler.resolve(), a.frontend.resolve(),
            a.tape.resolve(), a.rom.resolve(),
            stack=a.stack, maximum=a.max, use_fit=not a.no_fit)
        output = text.encode('ascii') if a.S else obj if a.c else ssx
        if a.output.resolve() == a.source.resolve():
            raise ValueError('refusing to overwrite original BASIC input')
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_bytes(output)
        if a.report:
            a.report.parent.mkdir(parents=True, exist_ok=True)
            a.report.write_text(json.dumps(report, indent=2) + '\n')
        print(f'RBC_NATIVE_OK file={report["file"]} image={report["image"]} '
              f'bss={report["bss"]} stack={report["stack"]} '
              f'total={report["total"]} relocs={report["relocations"]}')
        return 0
    except Exception as exc:
        print(f'RBC_NATIVE_BLOCKED {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
