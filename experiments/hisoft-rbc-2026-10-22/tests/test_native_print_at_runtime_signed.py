"""Two original ROM signed-coordinate cases in native ZX-UX execution."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
from native_wrapper_source import assemble_link, _signed_print_at
import rvm
import rld

SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'

# Original HiSoft PRINT_AT routine, with its individually witnessed labels.
SOURCE = '''    section text
    global start
start:
    ld de,65535
    ld hl,7
    call source_0010
    ld de,6
    ld hl,65535
    call source_0010
    ret
source_0010:
original_rt_0010:
    ld a, 0x16
original_rt_0012:
    rst 0x10
original_rt_0013:
    ld a, e
original_rt_0014:
    rst 0x10
original_rt_0015:
    ld a, l
original_rt_0016:
    rst 0x10
original_rt_0017:
    ret
    section bss
    ds 4
'''


class SignedAt(unittest.TestCase):
    def test_original_runtime_is_witnessed_and_modified_in_place(self):
        changed, count = _signed_print_at(SOURCE)
        self.assertEqual(count, 1)
        self.assertIn('rbc_wrapper_at_row_abs:', changed)
        self.assertIn('rbc_wrapper_at_col_abs:', changed)
        self.assertEqual(changed.count('    call source_0010'), 2)
        self.assertNotIn('rbc_at_signed_bridge', changed)
        with self.assertRaises(ValueError):
            _signed_print_at(SOURCE.replace('    ld a, e', '    ld a, d'))

    @unittest.skipUnless(SYSTEM.is_file() and FROZEN.is_file(),
                         'real ZX-UX system tape required')
    def test_native_rom_handles_negative_row_and_column(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        _, obj, ssx = assemble_link(SOURCE, bytes(768), use_rom_font=True,
                                    signed_print_at=True)
        self.assertTrue(obj)
        self.assertLessEqual(len(ssx), 14000)
        image = rld.parse_ssx(ssx)
        for base in (0x8100, 0x9100, 0xa000):
            moved, bss, entry, _, _ = rld.link(
                [rld.Obj(obj, 'native-at.sso')], [], entry='start',
                stack=384, org=base)
            self.assertEqual(moved, rld.relocate(image['image'], image['relocs'], base))
            self.assertEqual((bss, entry), (image['bss'], image['entry']))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'native-at.ssx'
            path.write_bytes(ssx)
            opts = rvm.Options()
            opts.prog, opts.keys, opts.frames = str(path), '', 800
            opts.system, opts.cache, opts.headless = str(SYSTEM), True, True
            run = rvm.Runner(opts)
            run.start()
            seen = []
            def capture(machine):
                seen.append((machine.cpu.b, machine.cpu.c))
                return False
            run.session.m.hooks[0x0a9b] = capture
            for _ in range(800):
                run.frame()
                if run.fg.ended is not None:
                    break
            self.assertIn((1, 7), seen)
            self.assertIn((6, 1), seen)
            self.assertIsNotNone(run.fg.ended)
            self.assertEqual(run.fg.status, 0)
            self.assertFalse(run.session.owns_screen(run.fg.pid))


if __name__ == '__main__':
    unittest.main()
