"""ROM is not zero-filled user memory in a native comparison."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import NativeProbeBlocked, compare_native_probes


def linked(source):
    obj = ras.assemble_text('    section text\n    global start\nstart:\n'
                            + source, 'rom-read-check.s')
    return rld.link([rld.Obj(obj, 'rom-read-check.sso')], [],
                    entry='start', stack=384)[0]


class ROMReads(unittest.TestCase):
    def test_absolute_rom_reads_fail_closed(self):
        for source in ('ld a,(56)', 'ld hl,(16383)', 'ld hl,0\n    ld a,(hl)'):
            with self.subTest(source=source):
                native = linked('    ' + source + '\n    ret\n')
                with self.assertRaisesRegex(NativeProbeBlocked, 'unmodelled ROM'):
                    compare_native_probes(native, native,
                                          bases=(0x6000,), flags=(0,), limit=32)

    def test_ram_read_is_still_compared(self):
        native = linked('    ld a,(23692)\n    ret\n')
        result = compare_native_probes(native, native,
                                       bases=(0x6000,), flags=(0,), limit=32)
        self.assertEqual(result['checked_exits'], 1)
        self.assertTrue(result['bounded_exit_states_match'])
        self.assertFalse(result['native_behavior_verified'])


if __name__ == '__main__':
    unittest.main()
