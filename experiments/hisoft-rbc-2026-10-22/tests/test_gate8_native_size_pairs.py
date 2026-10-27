"""Native, independently decoded file/image/BSS/stack accounting."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from symbolic_z80 import SymbolicProgram
from gate8_native_size_pairs import (NativeSizeError, dimensions,
                                     published_baselines, typed_pair)


class NativeDimensions(unittest.TestCase):
    def example(self):
        p = SymbolicProgram()
        p.label('start', entry=True)
        p.instruction('ld a,0')
        p.instruction('or b')
        p.instruction('ret')
        p.section('data')
        p.binary(b'\xc3\x18\x76')
        p.section('bss')
        p.reserve(8)
        return p

    def test_typed_native_pair_is_measured_at_both_actual_links(self):
        p = self.example()
        plain, before = p.optimize(lambda s: s, ras, rld)
        returned, after = p.optimize(lambda s: s.replace('    ld a,0\n',
                                                        '    xor a\n'), ras, rld)
        self.assertEqual(returned, plain)
        self.assertFalse(after['optimizer_admitted'])
        # A diagnostic native pair measures the linked candidate separately;
        # it is not the executable returned by the source pipeline.
        candidate_obj = ras.assemble_text(
            p.assembly().replace('    ld a,0\n', '    xor a\n'), 'size-candidate.s')
        changed, *_ = rld.link([rld.Obj(candidate_obj, 'size-candidate.sso')], [],
                               entry='start', stack=384)
        result = typed_pair(plain, changed, rld, source_verified=True,
                            native_behavior_verified=False)
        self.assertEqual(result['file_savings_bytes'], 1)
        self.assertEqual(result['memory_savings_bytes'], 1)
        self.assertEqual(result['pre_native']['file_bytes'], len(plain))
        self.assertEqual(result['post_native']['file_bytes'], len(changed))
        self.assertEqual(result['pre_native']['total_bytes'],
                         before['baseline_total_bytes'])
        self.assertEqual(result['post_native']['total_bytes'],
                         after['optimizer_candidate_total_bytes'])
        self.assertEqual(result['pre_native']['bss_bytes'], 8)
        self.assertEqual(result['post_native']['bss_bytes'], 8)
        self.assertFalse(result['native_behavior_verified'])
        self.assertFalse(result['upeepz80_revision_verified'])

    def test_fail_closed_without_complete_original_source(self):
        p = self.example()
        ssx, _ = p.optimize(lambda s: s, ras, rld)
        with self.assertRaisesRegex(NativeSizeError, 'typed complete'):
            typed_pair(ssx, ssx, rld, source_verified=False,
                       native_behavior_verified=True)
        with self.assertRaises(NativeSizeError):
            dimensions(b'not-ssx', rld)

    def test_unverified_size_pair_cannot_claim_native_behavior(self):
        obj = ras.assemble_text(self.example().assembly(), 'size-gate.s')
        linked = rld.link([rld.Obj(obj, 'size-gate.sso')], [],
                          entry='start', stack=384)[0]
        with self.assertRaisesRegex(NativeSizeError, 'cannot be asserted'):
            typed_pair(linked, linked, rld, source_verified=True,
                       native_behavior_verified=True)
        with self.assertRaisesRegex(NativeSizeError, 'cannot be asserted'):
            typed_pair(linked, linked, rld, source_verified=True,
                       native_behavior_verified=None)
        report = typed_pair(linked, linked, rld, source_verified=True,
                            native_behavior_verified=False)
        self.assertFalse(report['native_behavior_verified'])
        self.assertEqual(report['file_savings_bytes'], 0)

    def test_published_data_must_not_be_claimed_post_optimizer(self):
        report = published_baselines(ROOT, rld)
        self.assertEqual(report['original_bas'], 60)
        self.assertEqual(report['original_tzx'], 60)
        self.assertEqual(report['ssx'], 24)
        self.assertEqual(report['readmes'], 36)
        self.assertIsNone(report['post_upeep'])
        self.assertIsNone(report['optimizer_savings'])
        self.assertFalse(report['whole_program_optimized'])
        for entry in report['measurements']:
            self.assertEqual(entry['admission_bytes'],
                             max(entry['file_bytes'], entry['total_bytes']))
            self.assertEqual(entry['total_bytes'], entry['image_bytes'] +
                             entry['bss_bytes'] + entry['stack_bytes'])
            self.assertEqual(entry['stack_bytes'], 384)
            self.assertLessEqual(entry['admission_bytes'], 12000)

    def test_extra_bin_output_or_missing_original_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            corpus = root / 'src/bonus/60-programs'
            for i in range(60):
                game = corpus / f'{i:02}-example'
                (game / 'BASIC').mkdir(parents=True)
                (game / 'bin').mkdir()
                for ext in ('bas', 'tzx'):
                    (game / 'BASIC' / (game.name + '.' + ext)).write_bytes(b'original')
                (game / 'bin' / 'README.md').write_text('unsupported\n')
            with self.assertRaisesRegex(NativeSizeError, '24 checked'):
                published_baselines(root, rld)
            (corpus / '00-example' / 'bin' / 'extra.ssx').write_bytes(b'bad')
            with self.assertRaisesRegex(NativeSizeError, 'one published output'):
                published_baselines(root, rld)


if __name__ == '__main__':
    unittest.main()
