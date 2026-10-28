"""Bounded research fixture for a source-authored ZX-UX/HiSoft INPUT bridge.

This is NOT the production RBC path: original ROM EDITOR remains in the
published compiler. The fixture makes a witnessed *pre-link source* change,
then assembles/links with ras/rld and boots the frozen ZX-UX kernel. No SSX
patches, original-game edits, keyboard hooks or emulated success are involved.
"""
from pathlib import Path
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
import rvm
from native_rbc_cli import compile_native

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (CHECKPOINT / 'rbc.py',
    CHECKPOINT / 'font32.bin', FRONTEND / 'compiler.py', TAPE, ROM,
    SYSTEM, FROZEN))

# Kernel read(0) obtains the *original* physical keyboard events already
# decoded into /dev/tty.  ROM 1652 is the original one-character line-room
# operation.  No new data addresses, process-wide hooks or binary edits.
# Unbounded line length, error paths and full ROM edit controls are NOT yet
# established: this module is deliberately not installed into RBC.
EDITOR = '''rbc_test_input_editor:
    ld hl,($5c61)
    push hl
rbc_test_input_poll:
    ld hl,0
    ld de,($5c5b)
    ld bc,1
    ld a,3
    call $6003
    jr c,rbc_test_input_done
    ld a,h
    or l
    jr z,rbc_test_input_done
    ld hl,($5c5b)
    ld a,(hl)
    cp 10
    jr z,rbc_test_input_done
    push af
    ld (hl),13
    call $1652
    pop af
    ld (de),a
    inc de
    ld ($5c5b),de
    jr rbc_test_input_poll
rbc_test_input_done:
    ld hl,($5c5b)
    ld (hl),13
    pop hl
    ld ($5c61),hl
    ret
'''


def link_candidate(source):
    if source.count('    call 0x0f2c\n') != 1 or not any(
            line.startswith('original_rt_') and line.endswith(':')
            for line in source.splitlines()):
        raise ValueError('original HiSoft ROM EDITOR call/source witness missing')
    if source.count('    section data\n') != 1:
        raise ValueError('original section layout unexpected')
    changed = source.replace('    call 0x0f2c\n',
                             '    call rbc_test_input_editor\n', 1)
    changed = changed.replace('    section data\n',
                              EDITOR + '    section data\n', 1)
    obj = ras.assemble_text(changed, 'native-input-source-fixture.s')
    linked, *_ = rld.link([rld.Obj(obj, 'native-input-source-fixture.sso')],
                          [], entry='start', stack=384)
    parsed = rld.parse_ssx(linked)
    total = len(parsed['image']) + parsed['bss'] + parsed['stack']
    if parsed['entry'] != 0 or max(total, len(linked)) > 14000:
        raise ValueError('experimental input source fails loader limits')
    return linked


@unittest.skipUnless(READY, 'requires original compiler, tape, ROM and ZX-UX')
class NativeInputSourceCandidate(unittest.TestCase):
    def test_rom_editor_is_blocked_but_bounded_tty_source_can_read(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        fixtures = (
            ('10 REM : OPEN #\n20 INPUT A$\n'
             '30 IF A$="abc" THEN POKE 22528,55\n40 STOP\n',
             {'abc': 55, 'xxx': 7, '1234': 7}),
            ('10 REM : OPEN #\n20 INPUT A$\n'
             '30 POKE 22528,LEN A$+20\n40 STOP\n',
             {'abc': 23, 'xxx': 23, '1234': 24, '': 20}),
            ('10 REM : OPEN #\n20 INPUT A\n'
             '30 IF A=1234 THEN POKE 22528,55\n40 STOP\n',
             {'1234': 55, '999': 7, '123x{DELETE}4': 55,
              'abc{ENTER}{WAIT 100}1234': 55}),
        )
        with tempfile.TemporaryDirectory(prefix='rbc-input-source-') as tmp:
            for i, (basic, cases) in enumerate(fixtures):
                with self.subTest(fixture=i):
                    bas = Path(tmp) / ('input-%d.bas' % i)
                    ssx = Path(tmp) / ('input-%d.ssx' % i)
                    bas.write_text(basic, encoding='ascii')
                    asm, _, legacy, proof = compile_native(
                        bas, CHECKPOINT, FRONTEND, TAPE, ROM)
                    self.assertTrue(proof['native_three_base_source_verified'])
                    self.assertTrue(proof['native_and_legacy_ssx_byte_identical'])
                    self.assertFalse(proof['optimizer_used'])
                    self.assertNotEqual(link_candidate(asm), legacy)
                    ssx.write_bytes(link_candidate(asm))
                    for keys, marker in cases.items():
                        with self.subTest(fixture=i, keys=keys):
                            runner = rvm.run_kernel(
                                ssx, keys='{WAIT 200}' + keys + '{ENTER}',
                                frames=1400, system=SYSTEM)
                            self.assertEqual(runner.why, 'exit')
                            self.assertEqual(runner.fg.status, 0)
                            self.assertIsNotNone(runner.fg.exit_picture)
                            self.assertEqual(runner.fg.exit_picture[0][6144], marker)
                            runner.session.wait_prompt(1500)
                            self.assertEqual(runner.session.last_line(), '#')
                            self.assertFalse(runner.session.owns_screen(runner.fg.pid))


if __name__ == '__main__':
    unittest.main()
