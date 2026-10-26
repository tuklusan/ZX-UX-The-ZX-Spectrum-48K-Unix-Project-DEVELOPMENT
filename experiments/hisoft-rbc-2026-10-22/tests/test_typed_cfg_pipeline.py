"""Native three-pass end-to-end source/CFC linking; no gameplay claim."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from symbolic_capture import Emission
from typed_whole_pipeline import verify_and_build, link_source_pair, SourcePipelineError


def assemble(source):
    if source == 'jp nn':
        return b'\xc3'
    if source.startswith('jp '):
        return b'\xc3' + int(source[3:]).to_bytes(2, 'little')
    if source == 'nop':
        return b'\x00'
    if source == 'ret':
        return b'\xc9'
    raise ValueError(source)


def passes():
    bases = (0x6000, 0x6100, 0x6200)
    records = []
    images = []
    for base in bases:
        word = (base + 4).to_bytes(2, 'little')
        records.append((Emission(0, 'opcode', 'jp nn', b'\xc3', source_site='emit_goto:100'),
                        Emission(1, 'word', '(0,)', b'\0\0', source_site='emit_word:101'),
                        Emission(3, 'instruction', 'nop', b'\0', source_site='emit:102'),
                        Emission(4, 'instruction', 'ret', b'\xc9', source_site='emit:103'),
                        Emission(1, 'direct-write', 'st_next', word[:1]),
                        Emission(2, 'direct-write', 'st_next', word[1:])))
        images.append(b'\xc3' + word + b'\0\xc9')
    return records, images, bases, (5,) * 3, (8,) * 3


class NativeCFGIntegration(unittest.TestCase):
    def test_three_sourced_passes_link_native_without_optimizer_claim(self):
        verified = verify_and_build(*passes(), assemble)
        cfg = verified.source_report['whole_source_control_flow']
        self.assertEqual(cfg['source_cfg_verified_bases'], 3)
        self.assertEqual(cfg['source_cfg_entries'], 1)
        self.assertEqual(cfg['source_cfg_reachable_instructions'], 2)
        self.assertEqual(cfg['source_cfg_unreached_instructions'], 1)
        self.assertEqual(cfg['source_cfg_edges'], 1)
        plain, candidate, report = link_source_pair(verified, ras, rld, lambda x: x)
        self.assertEqual(plain, candidate)
        self.assertEqual(rld.parse_ssx(plain)['image'][0], 0xc3)
        self.assertFalse(report['native_behavior_verified'])

    def test_missing_source_entry_is_refused_before_link(self):
        with self.assertRaisesRegex(SourcePipelineError, 'CFG entry'):
            verify_and_build(*passes(), assemble, entry_offsets=(1,))


if __name__ == '__main__':
    unittest.main()
