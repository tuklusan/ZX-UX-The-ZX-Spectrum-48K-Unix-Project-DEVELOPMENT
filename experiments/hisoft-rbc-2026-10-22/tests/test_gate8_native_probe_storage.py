"""Bounded native probes must account for the loader's entire allocation."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import NativeProbeBlocked, compare_native_probes


def native_with_bss(count: int, stack: int = 384) -> bytes:
    source = ('    section text\n    global start\nstart:\n    ret\n'
              '    section bss\n    defs ' + str(count) + '\n')
    obj = ras.assemble_text(source, 'native-storage-probe.s')
    return rld.link([rld.Obj(obj, 'native-storage-probe.sso')], [],
                    entry='start', stack=stack)[0]


class BoundedStorage(unittest.TestCase):
    def test_oversized_bss_rejected_before_running_any_instruction(self):
        native = native_with_bss(20000)
        info = rld.parse_ssx(native)
        self.assertEqual(len(info['image']), 1)
        self.assertGreater(len(info['image']) + info['bss'] + info['stack'], 16384)
        with self.assertRaisesRegex(NativeProbeBlocked, 'image/BSS/stack outside'):
            compare_native_probes(native, native, bases=(0x6000,), flags=(0,))

    def test_same_image_fits_lower_base_but_not_higher_base(self):
        native = native_with_bss(8000)
        success = compare_native_probes(native, native,
                                        bases=(0x6000,), flags=(0,), limit=1)
        self.assertEqual(success['checked_exits'], 1)
        self.assertTrue(success['bounded_exit_states_match'])
        with self.assertRaisesRegex(NativeProbeBlocked, 'image/BSS/stack outside'):
            compare_native_probes(native, native,
                                  bases=(0x8000,), flags=(0,), limit=1)

    def test_oversized_declared_stack_is_not_ignored(self):
        native = native_with_bss(1, stack=20000)
        with self.assertRaisesRegex(NativeProbeBlocked, 'image/BSS/stack outside'):
            compare_native_probes(native, native, bases=(0x6000,), flags=(0,))


if __name__ == '__main__':
    unittest.main()
