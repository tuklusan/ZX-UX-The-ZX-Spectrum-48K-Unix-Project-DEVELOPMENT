"""Compile original Tug of War and witness correctly sized native string rows.

Opt-in original HiSoft frontend and compiler tape are needed. The test builds
only untracked temporary SSX output. It never rewrites the published game.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
GAME = ROOT / 'src/bonus/60-programs/03-tug-of-war'
BAS = GAME / 'BASIC/03-tug-of-war.bas'
TZX = GAME / 'BASIC/03-tug-of-war.tzx'
ORIGINAL = GAME / 'bin/03-tug-of-war.ssx'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
CHECKPOINT = Path(os.environ.get('RBC_TUG_CHECKPOINT_DIR', '/nonexistent'))
FRONTEND = Path(os.environ.get('RBC_FRONTEND_DIR', '/nonexistent'))
TAPE = Path(os.environ.get('RBC_HISOFT_TAPE', '/nonexistent'))
READY = all(p.is_file() for p in (
    BAS, TZX, ORIGINAL, ROM, SYSTEM, FROZEN, CHECKPOINT/'rbc.py',
    CHECKPOINT/'native_string_redim.py', FRONTEND/'compiler.py', TAPE))


def word(mem, address):
    return mem[address] | (mem[address + 1] << 8)


@unittest.skipUnless(READY, 'requires rebuilt RBC, original HiSoft tape, and canonical frontend')
class NativeTugStringRows(unittest.TestCase):
    def test_original_native_recompile_initializes_six_byte_rows(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        source = tuple(p.read_bytes() for p in (BAS, TZX, ORIGINAL, ROM))
        self.assertEqual(hashlib.sha256(source[1]).hexdigest(),
                         '10c4a2cffbdfec0e6917a4a7ecd311e01a074f61c297b35ca29053d7bbcfdea4')
        self.assertEqual(source[2][:4], b'SSX1')
        self.assertEqual(CHECKPOINT.joinpath('native_string_redim.py').read_bytes(),
                         STAGE.joinpath('native_string_redim.py').read_bytes())
        sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
        import rld
        import rvm
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'recompiled-tug.ssx'
            cmd = [sys.executable, '-B', str(STAGE / 'native_rbc_cli.py'),
                   str(BAS), '--compiler', str(CHECKPOINT),
                   '--frontend', str(FRONTEND), '--tape', str(TAPE),
                   '--rom', str(ROM), '--input-backend', 'rom',
                   '-o', str(target)]
            result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                    timeout=160)
            self.assertEqual(result.returncode, 0, result.stderr)
            native = target.read_bytes()
            self.assertNotEqual(native, source[2])
            parsed = rld.parse_ssx(native)
            self.assertEqual(parsed['entry'], 0)
            self.assertLessEqual(max(len(native), len(parsed['image']) +
                                     parsed['bss'] + parsed['stack']), 14000)
            run = rvm.run_kernel(target, keys='', frames=400, system=SYSTEM)
            self.assertIsNotNone(run.fg.started)
            machine = run.session.m
            observed = []
            def at_rom_make_room(z):
                c = z.cpu
                observed.append((c.b << 8) | c.c)
                return False
            self.assertNotIn(0x2b7f, machine.hooks)
            machine.hooks[0x2b7f] = at_rom_make_room
            run.session.kb.type('a')
            for _ in range(450):
                run.frame()
            self.assertGreaterEqual(len(observed), 4)
            self.assertEqual(observed[:4], [6, 6, 6, 6])
            self.assertEqual(word(machine.mem, 0xf1ae), 6)
            self.assertEqual(word(machine.mem, 0xf1bc), 2)
            self.assertEqual(word(machine.mem, 0xf1be), 6)
            self.assertEqual(word(machine.mem, 0xf1cc), 2)
            self.assertEqual(machine.mem[0x5c3a], 255)  # no ROM error
            self.assertIsNone(run.fg.ended)
            self.assertTrue(run.session.owns_screen(run.fg.pid))
            picture, _ = run.picture()
            self.assertEqual(len(picture), 6912)
            self.assertEqual(tuple(p.read_bytes() for p in (BAS, TZX, ORIGINAL, ROM)),
                             source)


if __name__ == '__main__':
    unittest.main()
