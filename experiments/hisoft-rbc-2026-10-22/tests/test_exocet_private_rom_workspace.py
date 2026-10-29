"""Real ZX-UX regression: Exocet's string-work buffer must not hit kernel RAM."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import rld
import rvm
from native_rbc_cli import compile_native
from native_string_compiler import with_static_strings
from native_long_string_proof import bounded_growth, workspace_bytes
from native_wrapper_source import assemble_link

GAME = ROOT / 'src/bonus/60-programs/47-exocet'
SOURCE = GAME / 'BASIC/47-exocet.bas'
TZX = GAME / 'BASIC/47-exocet.tzx'
SSX = GAME / 'bin/47-exocet.ssx'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
CK = ROOT / 'build/tmp/rbc-current-exocet-candidate/rbc'
FE = ROOT / 'build/tmp/tug-fault-investigation/frontend/upstream-pyhsb'
TAPE = ROOT / 'build/tmp/hisoft-test-original.tap'
READY = all(x.is_file() for x in (SOURCE, TZX, SSX, ROM, SYSTEM, FROZEN, CK/'rbc.py', FE/'compiler.py', TAPE))


class StringProof(unittest.TestCase):
    def test_proof_is_exact_and_fails_closed(self):
        proof = bounded_growth(SOURCE)
        self.assertEqual(proof[0]['max_chars'], 664)
        self.assertEqual(workspace_bytes(proof), 1024)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'edited.bas'
            p.write_bytes(SOURCE.read_bytes().replace(b'FOR x=1 TO 100',b'FOR x=1 TO 101'))
            self.assertEqual(bounded_growth(p), [])
            self.assertEqual(workspace_bytes(bounded_growth(p)), 0)

    def test_large_static_capacity_is_locked_to_original_proof(self):
        class Empty:
            pass
        def letter(_):
            return 0
        proof = {'variable':'S$', 'max_chars':664,
                 'bound_proof':'original-exocet-bounded-concatenation'}
        self.assertIsNot(with_static_strings(Empty,[proof],letter),Empty)
        with self.assertRaises(ValueError):
            with_static_strings(Empty,[{**proof,'max_chars':665}],letter)
        with self.assertRaises(ValueError):
            with_static_strings(Empty,[{**proof,'bound_proof':'unverified'}],letter)

    def test_private_workspace_emission_and_restore(self):
        source = ('    section text\n    global start\nstart:\n    ret\n'
                  '    section bss\n    ds 4\n')
        text, obj, ssx = assemble_link(source, bytes(768), use_rom_font=True,
                                       rom_work_bytes=1024)
        self.assertIn('rbc_wrapper_rom_work:\n    ds 1024', text)
        for ptr in ('5c61', '5c63', '5c65'):
            self.assertIn('rbc_wrapper_saved_work_' + ptr, text)
        self.assertLessEqual(len(ssx), 14000)
        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp) / 'rom-work-exit.ssx'
            executable.write_bytes(ssx)
            session = rvm.run_kernel(executable, keys='', frames=800,
                                     system=SYSTEM)
            self.assertEqual(session.why, 'exit', session.summary())
            self.assertEqual(session.fg.status, 0)
            self.assertFalse(session.session.owns_screen(session.fg.pid))
            # The shell must not retain any private ROM work pointers.
            for addr in (0x5c61, 0x5c63, 0x5c65):
                ptr = session.session.m.mem[addr] | (session.session.m.mem[addr+1] << 8)
                self.assertLess(ptr, 0x8000)


@unittest.skipUnless(READY, 'requires real recovered HiSoft frontend, 48K ROM and ZX-UX')
class RealExocet(unittest.TestCase):
    def test_original_compiler_string_work_owns_private_memory(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        preserved = tuple(x.read_bytes() for x in (SOURCE,TZX,SSX,ROM))
        baseline = hashlib.sha256(preserved[2]).hexdigest()
        asm, obj, ssx, report = compile_native(SOURCE, CK, FE, TAPE, ROM)
        self.assertTrue(report['native_three_base_source_verified'])
        self.assertEqual(report['rom_work_bytes'], 1024)
        self.assertEqual(report['source_proven_string_growth'][0]['max_chars'], 664)
        self.assertEqual(report['original_hisoft_baseline_sha256'] != report['native_ssx_sha256'], True)
        self.assertLessEqual(max(report['file'],report['total']), 14000)
        self.assertFalse(report['optimizer_used'])
        self.assertEqual(report['input_backend'], 'rom')
        self.assertIn('rbc_wrapper_rom_work:',asm)
        self.assertNotEqual(ssx,preserved[2])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'exocet-test.ssx'
            path.write_bytes(ssx)
            run = rvm.run_kernel(path, keys='', frames=400, system=SYSTEM)
            self.assertIsNotNone(run.fg.started)
            m=run.session.m
            fault=[];invalid=[]
            def trap(z):
                fault.append((z.frame,z.mem[0x5c3a]));return False
            def print_at(z):
                c=z.cpu
                if c.b>21 or c.c>31: invalid.append((c.b,c.c))
                return False
            m.hooks[0x6060]=trap
            m.hooks[0x0a9b]=print_at
            run.session.kb.type('a')
            for _ in range(1400):
                run.frame()
                if fault or run.fg.ended is not None:
                    break
            self.assertFalse(fault)
            self.assertFalse(invalid)
            self.assertTrue(run.session.owns_screen(run.fg.pid))
            self.assertIsNone(run.fg.ended)
            self.assertNotEqual(m.mem[0x5c61] | (m.mem[0x5c62] << 8),0x5d45)
            # Kernel tape countdown must never become the ROM string's space byte.
            self.assertEqual(m.mem[0x5dcd],0)
        self.assertEqual(tuple(x.read_bytes() for x in (SOURCE,TZX,SSX,ROM)),preserved)
        self.assertEqual(hashlib.sha256(SSX.read_bytes()).hexdigest(),baseline)


if __name__ == '__main__':
    unittest.main()
