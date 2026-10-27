"""Native equivalence cannot pass with an empty or partial comparison matrix."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import NativeProbeBlocked, compare_native_probes


def ret_native():
    obj = ras.assemble_text('    section text\n    global start\nstart:\n    ret\n',
                            'native-probe-parameters.s')
    return rld.link([rld.Obj(obj, 'native-probe-parameters.sso')], [],
                    entry='start', stack=384)[0]


class ProbeParameters(unittest.TestCase):
    def test_empty_generator_cannot_claim_matching_exits(self):
        native = ret_native()
        for kwargs in ({'bases': iter(())}, {'flags': iter(())}):
            with self.subTest(kwargs=tuple(kwargs)):
                with self.assertRaisesRegex(NativeProbeBlocked, 'invalid bounded'):
                    compare_native_probes(native, native, **kwargs)

    def test_one_shot_flag_iterator_cannot_skip_later_bases(self):
        native = ret_native()
        with self.assertRaisesRegex(NativeProbeBlocked, 'invalid bounded'):
            compare_native_probes(native, native,
                                  bases=(0x6000, 0x7000), flags=iter((0, 1)))

    def test_finite_lists_check_every_base_and_flag(self):
        native = ret_native()
        report = compare_native_probes(native, native,
                                       bases=[0x6000, 0x7000], flags=[0, 1])
        self.assertEqual(report['checked_exits'], 4)
        self.assertTrue(report['bounded_exit_states_match'])
        self.assertFalse(report['native_behavior_verified'])


if __name__ == '__main__':
    unittest.main()
