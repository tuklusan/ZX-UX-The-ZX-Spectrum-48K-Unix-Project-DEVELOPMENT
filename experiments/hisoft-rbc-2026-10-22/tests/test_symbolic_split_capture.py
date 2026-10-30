"""HiSoft D+E journals must retain genuine code and DATA source ownership."""
from pathlib import Path
import os
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
from symbolic_capture import Capture, Emission, audit_result, merge_split_capture


def split():
    e = SimpleNamespace(ok=True, mode='E', code=b'\0\xc9', load=0x8000,
                        code_base=0x8000, var_bytes=10, mc_bytes=5)
    d = SimpleNamespace(ok=True, mode='D', code=b'abc', load=0x8002,
                        code_base=0x8000, var_bytes=10, mc_bytes=5)
    joined = SimpleNamespace(ok=True, mode='D+E', code=e.code + d.code,
                             load=e.load, var_bytes=10, parts=[d, e])
    journals = {
        'E': Capture(events=[Emission(0, 'instruction', 'nop', b'\0'),
                             Emission(1, 'instruction', 'ret', b'\xc9')]),
        'D': Capture(events=[Emission(2, 'data-source', 'BASIC line 10 DATA', b'abc')]),
    }
    return joined, journals


class SplitCaptureTests(unittest.TestCase):
    def test_original_halves_cover_joined_bytes(self):
        whole, halves = split()
        capture = merge_split_capture(whole, halves)
        compiler = SimpleNamespace(_zxux_capture=capture, data_start=2)
        report = audit_result(compiler, whole)
        self.assertEqual(report['uncovered_bytes'], 0)
        self.assertEqual(report['changed_after_emit'], 0)
        self.assertEqual([event.kind for event in capture.events],
                         ['instruction', 'instruction', 'data-source'])

    def test_c_and_split_data_source_order_agree(self):
        whole, halves = split()
        original_c = Capture(events=[halves['E'].events[0],
                                     halves['D'].events[0],
                                     halves['E'].events[1]])
        c_result = SimpleNamespace(ok=True, mode='C', code=whole.code)
        compiler = SimpleNamespace(_zxux_capture=original_c, data_start=2)
        audit_result(compiler, c_result)
        joined = merge_split_capture(whole, halves)
        self.assertEqual(original_c.events, joined.events)

    def test_rejects_d_half_crossing_code_boundary(self):
        whole, halves = split()
        halves['D'].events.append(Emission(1, 'data-source', 'bad', b'x'))
        with self.assertRaisesRegex(ValueError, 'half boundary'):
            merge_split_capture(whole, halves)

    def test_rejects_e_half_crossing_data_boundary(self):
        whole, halves = split()
        halves['E'].events.append(Emission(2, 'instruction', 'bad', b'x'))
        with self.assertRaisesRegex(ValueError, 'half boundary'):
            merge_split_capture(whole, halves)

    def test_rejects_joined_bytes_not_from_original_halves(self):
        whole, halves = split()
        whole.code = b'\0\xc9abX'
        with self.assertRaisesRegex(ValueError, 'boundaries'):
            merge_split_capture(whole, halves)

    def test_rejects_missing_data_half_and_opaque_data(self):
        whole, halves = split()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            merge_split_capture(whole, {'E': halves['E']})
        halves['D'].events.append(Emission(2, 'runtime-opaque', 'bad', b'a'))
        with self.assertRaisesRegex(ValueError, 'half boundary'):
            merge_split_capture(whole, halves)

    def test_rejects_source_patch_within_data(self):
        whole, halves = split()
        c = Capture(events=halves['E'].events + halves['D'].events +
                    [Emission(2, 'direct-write', 'patch', b'z')])
        with self.assertRaisesRegex(ValueError, 'unverified source'):
            audit_result(SimpleNamespace(_zxux_capture=c, data_start=2),
                         SimpleNamespace(ok=True, mode='C', code=whole.code))


class RealSplitHiSoftSourceTests(unittest.TestCase):
    def test_three_original_split_programs_at_independent_bases(self):
        keys = ('RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE')
        paths = [os.environ.get(key) for key in keys]
        if not all(paths) or not all(Path(path).exists() for path in paths):
            self.skipTest('requires the recovered HiSoft compiler and original tape')
        from gate8_full_source_audit import run
        for game in ('13-radio-power', '19-hobday-expenses', '22-top-trainer'):
            with self.subTest(game=game):
                path = ROOT / 'src/bonus/60-programs' / game / 'BASIC' / (game + '.bas')
                result = run(path, Path(paths[0]), Path(paths[1]),
                             Path(paths[2]), ROOT / 'src/zx-ux-sdk/rom/48.rom',
                             max_bytes=40000)
                proof = result['native_whole_source_baseline']
                self.assertTrue(proof['native_whole_source_baseline_linked'])
                self.assertTrue(proof['native_image_byte_exact'])
                self.assertTrue(proof['all_source_relocations_verified'])
                self.assertEqual(proof['native_source_bases'], 3)
                self.assertGreater(max(proof['native_file_bytes'],
                                       proof['native_total_bytes']), 14000)
                self.assertFalse(proof['native_behavior_verified'])


if __name__ == '__main__':
    unittest.main()
