"""The native differential harness checks peak stack depth, not just final SP."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import NativeProbeBlocked, compare_native_probes


def stack_roundtrip(stack):
    # Six bytes are pushed and later restored. The final SP alone cannot
    # distinguish a valid six-byte allocation from a four-byte overflow.
    source = ("    section text\n    global start\nstart:\n"
              "    ld b,3\nloop_push:\n    push hl\n    djnz loop_push\n"
              "    ld b,3\nloop_pop:\n    pop hl\n    djnz loop_pop\n"
              "    ret\n")
    obj = ras.assemble_text(source, 'native-stack-depth.s')
    return rld.link([rld.Obj(obj, 'native-stack-depth.sso')], [],
                    entry='start', stack=stack)[0]


class NativeStackDepth(unittest.TestCase):
    def test_temporary_stack_overflow_cannot_be_hidden_by_pops(self):
        native = stack_roundtrip(4)
        with self.assertRaisesRegex(NativeProbeBlocked, 'declared stack'):
            compare_native_probes(native, native,
                                  bases=(0x6000,), flags=(0,), limit=100)

    def test_exactly_enough_stack_is_accepted(self):
        native = stack_roundtrip(6)
        result = compare_native_probes(native, native,
                                       bases=(0x6000,), flags=(0,), limit=100)
        self.assertEqual(result['checked_exits'], 1)
        self.assertTrue(result['bounded_exit_states_match'])
        self.assertFalse(result['native_behavior_verified'])

    def test_original_native_matrix_still_accepts_bounded_return(self):
        native = stack_roundtrip(384)
        result = compare_native_probes(native, native)
        self.assertEqual(result['checked_exits'], 12)
        self.assertTrue(result['bounded_exit_states_match'])


if __name__ == '__main__':
    unittest.main()
