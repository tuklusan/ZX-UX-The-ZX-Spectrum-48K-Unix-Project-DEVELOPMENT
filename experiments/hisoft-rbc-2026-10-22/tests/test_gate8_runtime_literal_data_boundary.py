"""Runtime literal RST/HALT-looking bytes must stay opaque to upeepz80."""
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from z80asm import asm
from runtime_emitter_trace import RuntimeEmitterTrace
from runtime_typed_source import RuntimeStatement, RuntimeSourceError, typed_runtime_events
from symbolic_capture import Emission
from symbolic_source_boundaries import inspect_source_boundaries
from typed_runtime_bridge import RuntimeWitness
from typed_whole_pipeline import verify_and_build_with_runtime_sources, link_source_pair
from gate8_native_whole_optimizer import verify_whole_optimizer_candidate, WholeOptimizerError

BASES = (0x6000, 0x6100, 0x6200)


@dataclass(frozen=True)
class Writer:
    position: int
    value: int
    emitter_pc: int


def records():
    groups, images, witnesses, reports = [], [], [], []
    for base in BASES:
        # Jump past "A;B", HALT-looking 0x76 data to a real RET.
        data = b'\xc3' + (base + 7).to_bytes(2, 'little') + b'A;B\x76\xc9'
        sites = (0x7001,) * 3 + (0x7002,) * 4 + (0x7003,)
        writes = tuple(Writer(i, byte, sites[i]) for i, byte in enumerate(data))
        statements = (
            RuntimeStatement(0, 0x7001, 'relocated', 'jp nn', 7),
            RuntimeStatement(3, 0x7002, 'literal', 'defb 65,59,66,118'),
            RuntimeStatement(7, 0x7003, 'instruction', 'ret'),
        )
        memory = bytearray(65536)
        def wb(address, value):
            memory[address & 0xffff] = value & 255
        cpu = SimpleNamespace(mem=memory, wb=wb, trace=None)
        machine = SimpleNamespace(p={'direct': True, 'staging': 0x9000}, cpu=cpu)
        with RuntimeEmitterTrace(machine) as trace:
            for record in writes:
                cpu.trace(record.emitter_pc)
                cpu.wb(0x9000 + record.position, record.value)
        report = trace.inspect(0, len(data), data)
        report['routine'] = 27
        groups.append((Emission(0, 'runtime-opaque', 'RT27', data),))
        images.append(data)
        witnesses.append((RuntimeWitness(27, 0, len(data), writes, statements),))
        reports.append((report,))
    return groups, images, witnesses, reports


class OriginalRuntimeOpaqueLiteralTests(unittest.TestCase):
    def test_three_base_runtime_literal_is_data_not_halt_instruction(self):
        groups, images, witnesses, reports = records()
        for data, witness, base in zip(images, witnesses, BASES):
            events = typed_runtime_events(witness[0].writes,
                                          witness[0].statements, data,
                                          0, len(data), base, asm)
            self.assertEqual([e.kind for e in events],
                             ['opcode', 'relocation', 'inline-data', 'instruction'])
            source_map = inspect_source_boundaries(events, data, base,
                                                  len(data), 0, asm)
            self.assertTrue(source_map.fully_typed)
            self.assertEqual(source_map.executable_instruction_count, 2)
            self.assertEqual(source_map.instruction_bytes, 4)
        verified = verify_and_build_with_runtime_sources(
            groups, images, BASES, [8] * 3, [0] * 3, asm,
            witnesses, reports)
        assembly = verified.program.assembly()
        self.assertIn('db 65,59,66,118', assembly)
        self.assertNotIn('halt', assembly)
        native, unchanged, linked = link_source_pair(verified, ras, rld,
                                                     lambda text: text)
        self.assertEqual(native, unchanged)
        self.assertTrue(linked['native_links_verified'])
        plain = rld.parse_ssx(native)
        self.assertEqual(plain['image'][3:7], b'A;B\x76')
        for base, original in zip(BASES, images):
            self.assertEqual(bytes(rld.relocate(plain['image'],
                                                plain['relocs'], base)), original)
        with self.assertRaisesRegex(WholeOptimizerError, 'protected'):
            verify_whole_optimizer_candidate(
                assembly, native,
                lambda s: s.replace('db 65,59,66,118', 'db 65,59,66,119'))

    def test_original_runtime_source_literal_rejects_unquoted_comment(self):
        data = b'A;B'
        writes = tuple(Writer(i, byte, 0x7001) for i, byte in enumerate(data))
        def assembler(src):
            if src == 'defb "A;B"':
                return data
            if src == 'defb "A;B" ; not source':
                return data
            raise ValueError('unknown source')
        valid = typed_runtime_events(
            writes, (RuntimeStatement(0, 0x7001, 'literal', 'defb "A;B"'),),
            data, 0, 3, 0x6000, assembler)
        self.assertEqual(valid[0].kind, 'inline-data')
        for bad in ('defb "A;B" ; not source', 'defb "A;B', 'defb 65,59,66 ; tail'):
            with self.subTest(source=bad), self.assertRaises(RuntimeSourceError):
                typed_runtime_events(
                    writes, (RuntimeStatement(0, 0x7001, 'literal', bad),),
                    data, 0, 3, 0x6000, assembler)


if __name__ == '__main__':
    unittest.main()
