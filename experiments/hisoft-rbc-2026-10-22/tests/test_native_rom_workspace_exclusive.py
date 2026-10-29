"""Kernel ROM system variables are global; native workspace must fail closed."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
from native_wrapper_source import assemble_link
import rvm

SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'

# Two independent native SSX programs; neither refers to a BASIC game.
# Each reads the process-global WORKSP pointer while the 50Hz scheduler runs.
NATIVE = '''    section text
    global start
start:
    ld hl,($5c61)
    ld (hl),@MARK@
    ld hl,0
    ld a,38
    call $6003
    ld (first_tick),hl
again:
    ld hl,($5c61)
    ld a,(hl)
    cp @MARK@
    jr nz,wrong_owner
    ld hl,0
    ld a,38
    call $6003
    ld de,(first_tick)
    or a
    sbc hl,de
    ld de,900
    or a
    sbc hl,de
    jr c,again
    ret
wrong_owner:
    rst 8
    db 3
    section bss
first_tick:
    ds 2
'''


@unittest.skipUnless(SYSTEM.is_file() and FROZEN.is_file(),
                     'authentic ZX-UX system tape required')
class PrivateWorkspaceExclusive(unittest.TestCase):
    def test_concurrent_second_native_process_refused_without_rom_panic(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for name, marker in (('bg_workspace', 65), ('fg_workspace', 66)):
                source = NATIVE.replace('@MARK@', str(marker))
                emitted, obj, ssx = assemble_link(source, bytes(768),
                                                   use_rom_font=True,
                                                   rom_work_bytes=1024)
                self.assertIn('rbc_wrapper_screen_exclusive:', emitted)
                self.assertLessEqual(len(ssx), 14000)
                path = Path(directory) / (name + '.ssx')
                path.write_bytes(ssx)
                paths.append(path)
            opt = rvm.Options()
            opt.bg = [(str(paths[0]), [])]
            opt.prog, opt.keys, opt.frames = str(paths[1]), '', 800
            opt.system, opt.cache, opt.headless = str(SYSTEM), True, True
            run = rvm.Runner(opt)
            run.start()
            panic = []
            run.session.m.hooks[0x6048] = lambda z: panic.append(z.frame) or False
            overlap = False
            for _ in range(850):
                run.frame()
                if (run.fg.started is not None and
                        run.session.jobs[0].started is not None and
                        run.session.owns_screen(run.session.jobs[0].pid)):
                    overlap = True
                if panic or run.fg.ended is not None:
                    break
            self.assertTrue(overlap, 'must actually schedule a second process')
            self.assertFalse(panic, 'global ROM panic is not process isolation')
            self.assertIsNotNone(run.fg.ended)
            self.assertEqual(run.fg.status, 21,
                             'shared ROM workspace must not be activated twice')
            self.assertFalse(run.session.owns_screen(run.fg.pid))
            self.assertTrue(run.session.owns_screen(run.session.jobs[0].pid),
                            'declined process must not release the first screen')


if __name__ == '__main__':
    unittest.main()
