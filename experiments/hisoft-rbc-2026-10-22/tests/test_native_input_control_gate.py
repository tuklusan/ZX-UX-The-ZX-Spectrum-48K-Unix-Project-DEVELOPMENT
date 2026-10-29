"""Prevent unsupported ROM INPUT cursor/edit operations from corrupting text.

ZX-UX tty sends LEFT/DOWN/UP/RIGHT as bytes 8..11 and EDIT as 7. The
current bounded source reader cannot implement the original ROM cursor
editor; fail closed rather than inserting those bytes as printable text.
This test explicitly does NOT grant production ROM compatibility.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src/zx-ux-sdk'),
                str(ROOT / 'experiments/hisoft-rbc-2026-10-22/stage')]
import rvm
from native_rbc_cli import compile_native
from native_input_source import EDITOR

CHECKPOINT = ROOT / 'build/tmp/rbc-recovered/rbc'
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
READY = all(p.is_file() for p in (
    CHECKPOINT/'rbc.py', CHECKPOINT/'font32.bin', FRONTEND/'compiler.py',
    TAPE, ROM, SYSTEM, FROZEN))


class UnsupportedEditGate(unittest.TestCase):
    def test_control_keys_must_refuse_in_source(self):
        self.assertIn('    cp 7\n    jp z,rbc_raw_restore_abort\n'
                      '    cp 12\n    jp c,rbc_raw_restore_abort\n', EDITOR)
        self.assertNotIn('    cp 8\n    jp c,rbc_raw_poll\n', EDITOR)


@unittest.skipUnless(READY, 'checked native inputs required')
class NativeUnsupportedEditGate(unittest.TestCase):
    def test_key_edit_and_cursor_controls_exit_without_tty_or_shell_leak(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        with tempfile.TemporaryDirectory(prefix='rbc-input-edits-') as tmp:
            source = Path(tmp) / 'control.bas'
            executable = Path(tmp) / 'control.ssx'
            source.write_text('10 REM : OPEN #\n20 INPUT A$\n'
                              '30 POKE 22528,LEN A$+20\n40 STOP\n',
                              encoding='ascii')
            _, _, linked, report = compile_native(
                source, CHECKPOINT, FRONTEND, TAPE, ROM,
                input_backend='zxux')
            self.assertTrue(report['input_source_bridge_three_base_verified'])
            self.assertFalse(report['native_and_legacy_ssx_byte_identical'])
            executable.write_bytes(linked)
            for key in ('{LEFT}', '{RIGHT}', '{UP}', '{DOWN}', '{EDIT}'):
                with self.subTest(key=key):
                    run = rvm.run_kernel(
                        executable, keys='{WAIT 200}a'+key,
                        frames=900, system=SYSTEM)
                    self.assertEqual(run.why, 'exit', run.summary())
                    self.assertEqual(run.fg.status, 1, run.summary())
                    self.assertFalse(run.session.owns_screen(run.fg.pid))
                    run.session.wait_prompt(1500)
                    self.assertEqual(run.session.last_line(), '#')
            normal = rvm.run_kernel(executable,
                                    keys='{WAIT 200}abc{DELETE}d{ENTER}',
                                    frames=1100, system=SYSTEM)
            self.assertEqual(normal.why, 'exit', normal.summary())
            self.assertEqual(normal.fg.status, 0)
            self.assertEqual(normal.fg.exit_picture[0][6144], 23)
            normal.session.wait_prompt(1500)
            self.assertEqual(normal.session.last_line(), '#')


if __name__ == '__main__':
    unittest.main()
