"""Compare complete source compilation with passive typed-emission auditing.

No optimization is attempted. A different byte, missing producer or patched
address remains an unresolved Gate 8 boundary, never an optimizer success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import rld
from symbolic_capture import audit_result, install as install_capture
from symbolic_source_patches import from_emissions, verify_three_passes
from symbolic_relocations import inspect_relocations, verify_three_builds
from symbolic_instructions import inspect_sources, verify_three_sources
from symbolic_opcode_pairs import inspect_opcode_pairs, verify_three_opcode_passes
from symbolic_source_boundaries import inspect_source_boundaries, verify_three_source_maps
from symbolic_fragments import inspect_fragments, verify_three_fragment_passes
from runtime_emitter_trace import verify_three_runtime_traces
from symbolic_relative_branches import inspect_relative_branches, verify_three_relative_passes


def run(source: Path, checkpoint: Path, frontend: Path,
        tape: Path, rom: Path) -> dict:
    if not (checkpoint / 'rbc.py').is_file():
        raise ValueError('reconstructed RBC checkpoint required')
    if not (frontend / 'compiler.py').is_file():
        raise ValueError('canonical 48K frontend required')
    sys.path.insert(0, str(checkpoint))
    import rbc
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    baseline, _ = rbc._compile_three(source, frontend, tape, rom, 0xff00,
                                      [], 'block', False, 0)
    records = []
    source_words = []
    relocations = []
    instructions = []
    opcode_pairs = []
    source_maps = []
    source_fragments = []
    runtime_source_traces = []
    relative_groups = []
    original_hook = rbc.install_codegen_optimizer

    def passive_capture(module):
        install_capture(module)
        parent = module.Compiler.compile_whole
        def recorded(self, *args, **kwargs):
            result = parent(self, *args, **kwargs)
            if result.ok:
                records.append(audit_result(self, result))
                runtime_source_traces.append(list(self._zxux_capture.runtime_traces))
                source_words.append(from_emissions(
                    self._zxux_capture.events, result.code,
                    result.code_base, self.data_start))
                relocations.append(inspect_relocations(
                    self._zxux_capture.events, result.code,
                    result.code_base, result.var_bytes))
                from z80asm import asm
                instructions.append(inspect_sources(
                    self._zxux_capture.events, result.code, asm))
                opcode_pairs.append(inspect_opcode_pairs(
                    self._zxux_capture.events, result.code,
                    result.code_base, asm))
                source_map = inspect_source_boundaries(
                    self._zxux_capture.events, result.code,
                    result.code_base, self.data_start, result.var_bytes, asm)
                source_maps.append(source_map)
                relative_groups.append(inspect_relative_branches(
                    source_map.spans, self.data_start, asm))
                source_fragments.append(inspect_fragments(
                    self._zxux_capture.events, result.code, self.data_start, asm))
            return result
        module.Compiler.compile_whole = recorded

    try:
        rbc.install_codegen_optimizer = passive_capture
        observed, _ = rbc._compile_three(source, frontend, tape, rom,
                                          0xff00, [], 'block', True, 0)
    finally:
        rbc.install_codegen_optimizer = original_hook
    if len(baseline) != 3 or len(observed) != 3 or len(records) != 3:
        raise ValueError('requires three full compiler passes')
    for index, (before, after) in enumerate(zip(baseline, observed)):
        if (before.code, before.entry, before.base, before.bss) != (
                after.code, after.entry, after.base, after.bss):
            raise RuntimeError(f'passive capture changed program bytes at pass {index}')
    source_patch_report = verify_three_passes(source_words, observed)
    relocation_report = verify_three_builds(relocations, [x.base for x in observed])
    instruction_report = verify_three_sources(instructions, [x.base for x in observed])
    opcode_report = verify_three_opcode_passes(opcode_pairs, [x.base for x in observed])
    source_map_report = verify_three_source_maps(source_maps, [x.base for x in observed])
    fragment_report = verify_three_fragment_passes(source_fragments,
                                                 [x.base for x in observed])
    runtime_report = verify_three_runtime_traces(runtime_source_traces,
                                                 [x.base for x in observed])
    relative_report = verify_three_relative_passes(relative_groups,
                                                  [x.base for x in observed])
    first, _ = rbc.build_ssx(baseline, bytes(768), rld, 384, use_rom_font=True)
    second, _ = rbc.build_ssx(observed, bytes(768), rld, 384, use_rom_font=True)
    if first != second:
        raise RuntimeError('passive capture changed linked native program')
    info = rld.parse_ssx(first)
    total = len(info['image']) + info['bss'] + info['stack']
    if max(total, len(first)) > 12000:
        raise ValueError('default 12000-byte memory limit exceeded')
    for record in records:
        if record['safe_to_optimize']:
            raise RuntimeError('partial typed capture was incorrectly admitted')
    return {
        'source_sha256': source_hash, 'source': source.name,
        'passive_capture_byte_identical': True,
        'linked_sha256': hashlib.sha256(first).hexdigest(),
        'file': len(first), 'image': len(info['image']),
        'bss': info['bss'], 'stack': info['stack'], 'total': total,
        'audits': records, 'source_patches': source_patch_report,
        'source_relocations': relocation_report,
        'source_instructions': instruction_report,
        'paired_source_opcodes': opcode_report,
        'source_byte_ownership': source_map_report,
        'inline_source_fragments': fragment_report,
        'runtime_emitter_sources': runtime_report,
        'relative_source_branches': relative_report,
        'gate8_complete': False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--compiler', required=True, type=Path)
    p.add_argument('--frontend', required=True, type=Path)
    p.add_argument('--tape', required=True, type=Path)
    p.add_argument('--rom', type=Path, default=ROOT / 'src/zx-ux-sdk/rom/48.rom')
    args = p.parse_args()
    report = run(args.source.resolve(), args.compiler.resolve(),
                 args.frontend.resolve(), args.tape.resolve(), args.rom.resolve())
    print('GATE8_PASSIVE_SOURCE_AUDIT', json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
