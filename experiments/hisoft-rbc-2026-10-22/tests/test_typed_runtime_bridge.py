"""Source-owned runtime joins must survive three native links without guessing."""
from dataclasses import dataclass, replace
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
from z80_python.cpu import Z80CPU
from runtime_typed_source import RuntimeStatement
from runtime_emitter_trace import RuntimeEmitterTrace
from symbolic_capture import Emission
from typed_runtime_bridge import (RuntimeWitness, RuntimeBridgeError,
                                  splice_three_runtime_sources)
from typed_whole_pipeline import (verify_and_build_with_runtime_sources,
                                  link_source_pair)


@dataclass(frozen=True)
class Writer:
    position: int
    value: int
    emitter_pc: int


BASES = (0x6000, 0x6100, 0x6200)


def fixture():
    groups, images, witnesses, reports = [], [], [], []
    for base in BASES:
        image = b'\xc3' + (base + 3).to_bytes(2, 'little') + b'\xc9'
        events = (Emission(0, 'opcode', 'jp nn', b'\xc3', source_site='emit:10'),
                  Emission(1, 'relocation', '3', image[1:3], 3,
                           source_site='emit:11'),
                  Emission(3, 'runtime-opaque', 'RT27', b'\xc9',
                           source_site='runtime:27'))
        witness = RuntimeWitness(27, 3, 4, (Writer(3, 0xc9, 0x7100),),
                                 (RuntimeStatement(3, 0x7100, 'instruction',
                                                   'ret'),))
        groups.append(events)
        images.append(image)
        witnesses.append((witness,))
        memory = bytearray(65536)
        def wb(address, value):
            memory[address & 0xffff] = value & 255
        cpu = SimpleNamespace(mem=memory, wb=wb, trace=None)
        machine = SimpleNamespace(p={'direct': True, 'staging': 0x9000},
                                  cpu=cpu)
        with RuntimeEmitterTrace(machine) as trace:
            cpu.trace(0x7100)
            cpu.wb(0x9003, 0xc9)
        report = trace.inspect(3, 4, b'\xc9')
        report['routine'] = 27
        reports.append((report,))
    return groups, images, witnesses, reports


class RuntimeBridgeTests(unittest.TestCase):
    def test_three_base_source_handoff_and_native_relocation(self):
        groups, images, witnesses, reports = fixture()
        typed, info = splice_three_runtime_sources(
            groups, images, BASES, witnesses, asm, observed_traces=reports)
        self.assertTrue(info['typed_runtime_source_spliced'])
        self.assertEqual(info['runtime_source_bytes'], 1)
        self.assertEqual(typed[0][-1].source_site, 'runtime_pc:28928')
        self.assertEqual(typed[0][-1].producer_pcs, (0x7100,))
        self.assertEqual(groups[0][-1].kind, 'runtime-opaque')
        source = verify_and_build_with_runtime_sources(
            groups, images, BASES, [4] * 3, [0] * 3, asm, witnesses, reports)
        self.assertTrue(source.source_report['full_program_source_owned'])
        self.assertEqual(source.source_report['source_boundaries']['source_unresolved_bytes'], 0)
        self.assertEqual(source.program.assembly().count('ret'), 1)
        baseline, candidate, result = link_source_pair(source, ras, rld,
                                                       lambda text: text)
        self.assertEqual(baseline, candidate)
        self.assertTrue(result['native_links_verified'])
        self.assertFalse(result['native_behavior_verified'])
        native = rld.parse_ssx(baseline)
        self.assertEqual(native['image'], b'\xc3\x03\x00\xc9')
        for base in BASES:
            with self.subTest(base=base):
                memory = bytearray(65536)
                image = rld.relocate(native['image'], native['relocs'], base)
                memory[base:base + len(image)] = image
                memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                cpu.pc, cpu.sp = base, 0xd000
                for _ in range(8):
                    if cpu.pc == 0xb000:
                        break
                    cpu.step()
                else:
                    self.fail('native runtime branch did not return')
                self.assertEqual(cpu.sp, 0xd002)

    def test_missing_or_wrong_original_emitter_is_rejected(self):
        groups, images, witnesses, reports = fixture()
        for changed in ((), (replace(witnesses[0][0], number=28),),
                        (replace(witnesses[0][0], start=2),)):
            with self.subTest(changed=changed):
                mutant = [changed, witnesses[1], witnesses[2]]
                with self.assertRaises(RuntimeBridgeError):
                    splice_three_runtime_sources(groups, images, BASES, mutant, asm, observed_traces=reports)

    def test_unknown_vendor_runtime_number_is_rejected(self):
        groups, images, witnesses, reports = fixture()
        bogus = replace(groups[0][-1], source='RT999')
        with self.assertRaisesRegex(RuntimeBridgeError, 'original runtime source span'):
            splice_three_runtime_sources([groups[0][:-1] + (bogus,), *groups[1:]],
                                         images, BASES, witnesses, asm, observed_traces=reports)

    def test_untraced_rewrite_and_changed_source_are_rejected(self):
        groups, images, witnesses, reports = fixture()
        rewritten = tuple(groups[0]) + (Emission(3, 'byte', 'unknown', b'\xc9'),)
        with self.assertRaisesRegex(RuntimeBridgeError, 'rewrote runtime'):
            splice_three_runtime_sources([rewritten, *groups[1:]],
                                         images, BASES, witnesses, asm, observed_traces=reports)
        wrong_pc = replace(witnesses[1][0],
                           writes=(Writer(3, 0xc9, 0x7101),))
        with self.assertRaises(RuntimeBridgeError):
            splice_three_runtime_sources(groups, images, BASES,
                                         [witnesses[0], (wrong_pc,), witnesses[2]], asm,
                                         observed_traces=reports)
        wrong_statement = replace(witnesses[2][0],
                                  statements=(RuntimeStatement(3, 0x7100,
                                                               'instruction', 'nop'),))
        with self.assertRaises(RuntimeBridgeError):
            splice_three_runtime_sources(groups, images, BASES,
                                         [witnesses[0], witnesses[1],
                                          (wrong_statement,)], asm,
                                         observed_traces=reports)

    def test_byte_trace_alone_cannot_replace_runtime_source(self):
        groups, images, witnesses, reports = fixture()
        missing = replace(witnesses[0][0], statements=())
        with self.assertRaises(RuntimeBridgeError):
            splice_three_runtime_sources(groups, images, BASES,
                                         [(missing,), *witnesses[1:]], asm,
                                         observed_traces=reports)
        untyped = replace(witnesses[0][0],
                          statements=(RuntimeStatement(3, 0x7100, 'opaque', 'ret'),))
        with self.assertRaises(RuntimeBridgeError):
            splice_three_runtime_sources(groups, images, BASES,
                                         [(untyped,), *witnesses[1:]], asm,
                                         observed_traces=reports)

    def test_original_z80_trace_digest_and_completeness_are_required(self):
        groups, images, witnesses, reports = fixture()
        from copy import deepcopy
        for key, value in (('source_write_sites_sha256', '0' * 64),
                           ('fully_observed', False),
                           ('staging_write_count', 2),
                           ('outside_emitter_bytes', 1),
                           ('rewritten_bytes', 1),
                           ('routine', 28)):
            with self.subTest(key=key):
                bad = deepcopy(reports)
                bad[0] = (dict(bad[0][0], **{key: value}),)
                with self.assertRaises(RuntimeBridgeError):
                    splice_three_runtime_sources(groups, images, BASES,
                                                 witnesses, asm,
                                                 observed_traces=bad)
        with self.assertRaises(RuntimeBridgeError):
            splice_three_runtime_sources(groups, images, BASES, witnesses,
                                         asm, observed_traces=None)

    def test_reordered_runtime_write_sites_are_not_witnessed(self):
        groups, images, witnesses, reports = fixture()
        false = replace(witnesses[1][0],
                        writes=(Writer(3, 0xc9, 0x7000),),
                        statements=(RuntimeStatement(3, 0x7000,
                                                     'instruction', 'ret'),))
        with self.assertRaisesRegex(RuntimeBridgeError, 'differs from original'):
            splice_three_runtime_sources(groups, images, BASES,
                                         [witnesses[0], (false,), witnesses[2]],
                                         asm, observed_traces=reports)


if __name__ == '__main__':
    unittest.main()
