"""Native comparison must not model ROM memory as writable process RAM."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import NativeProbeBlocked, compare_native_probes


def executable_write(address):
    code = ('    section text\n    global start\nstart:\n'
            '    ld a,17\n    ld (' + str(address) + '),a\n    ret\n')
    obj = ras.assemble_text(code, 'native-rom-write.s')
    return rld.link([rld.Obj(obj, 'native-rom-write.sso')], [],
                    entry='start', stack=384)[0]


class NativeROMIsolation(unittest.TestCase):
    def test_native_rom_writes_are_rejected_even_for_identical_executables(self):
        for address in (0, 0x3fff):
            with self.subTest(address=address):
                code = executable_write(address)
                with self.assertRaisesRegex(NativeProbeBlocked, 'ROM write'):
                    compare_native_probes(code, code, bases=(0x6000,),
                                          flags=(0,), limit=16)

    def test_valid_screen_and_system_variable_writes_still_run(self):
        for address in (0x4000, 23692):
            with self.subTest(address=address):
                code = executable_write(address)
                result = compare_native_probes(code, code, bases=(0x6000,),
                                               flags=(0,), limit=16)
                self.assertEqual(result['checked_exits'], 1)
                self.assertTrue(result['bounded_exit_states_match'])
                self.assertFalse(result['native_behavior_verified'])


if __name__ == '__main__':
    unittest.main()
