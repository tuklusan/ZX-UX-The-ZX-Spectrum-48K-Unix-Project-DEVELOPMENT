"""Real ZX-UX regression: Exocet's string-work buffer must not hit kernel RAM."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
sys.path[:0] = [str(ROOT / 'build/tmp/tug-fault-investigation/frontend/upstream-pyhsb'), str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
import rld
import rvm
from native_rbc_cli import compile_native
from native_string_compiler import with_static_strings
from native_long_string_proof import growing_scalar_strings, workspace_bytes
import native_long_string_proof
from native_wrapper_source import assemble_link
from basic_listing import encode_strict_listing
from source import Keywords
from tap import split_lines

GAME = ROOT / 'src/bonus/60-programs/47-exocet'
SOURCE = GAME / 'BASIC/47-exocet.bas'
TZX = GAME / 'BASIC/47-exocet.tzx'
SSX = GAME / 'bin/47-exocet.ssx'
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
SYSTEM = ROOT / 'build/out/ZX-UX.tzx'
FROZEN = ROOT / 'dist/zx-ux/tzx/ZX-UX.tzx'
CK = ROOT / 'build/tmp/rbc-generic-candidate-3/rbc'
FE = ROOT / 'build/tmp/tug-fault-investigation/frontend/upstream-pyhsb'
TAPE = ROOT / 'build/tmp/hisoft-test-original.tap'
READY = all(x.is_file() for x in (SOURCE, TZX, SSX, ROM, SYSTEM, FROZEN, CK/'rbc.py', FE/'compiler.py', TAPE))


class StringProof(unittest.TestCase):
    def _proof(self, listing):
        tokenized = encode_strict_listing(listing)
        return growing_scalar_strings(tokenized, Keywords(ROM.read_bytes()), split_lines)

    def test_generic_token_selection_does_not_depend_on_source_hash_or_lines(self):
        original = SOURCE.read_text()
        proof = self._proof(original)
        self.assertEqual([(p['variable'], p['max_chars']) for p in proof],
                         [('S$', 1024)])
        self.assertEqual(workspace_bytes(proof), 2048)
        # Changing unrelated control flow and the basename cannot turn off
        # an operation-based memory-safety feature.
        self.assertEqual(self._proof(original.replace('FOR x=1 TO 100',
                                                      'FOR x=1 TO 101')), proof)
        unrelated = ('10 LET A$=""\n20 LET A$=A$+"x"\n'
                     '30 LET Z$="A$+"\n40 PRINT Z$\n')
        self.assertEqual([p['variable'] for p in self._proof(unrelated)], ['A$'])
        self.assertEqual(workspace_bytes(self._proof('10 PRINT "A$+"\n')), 0)

    def test_wide_capacity_is_generic_but_unproved_claim_is_rejected(self):
        class Empty:
            pass
        def letter(_):
            return 0
        proof = {'variable':'Y$', 'max_chars':2048,
                 'bound_proof':'native-runtime-checked-scalar-concatenation',
                 'storage_is_reservation': True}
        self.assertIsNot(with_static_strings(Empty,[proof],letter),Empty)
        with self.assertRaises(ValueError):
            with_static_strings(Empty,[{**proof,'max_chars':13001}],letter)
        with self.assertRaises(ValueError):
            with_static_strings(Empty,[{**proof,'bound_proof':'unverified'}],letter)

    def test_private_workspace_restores_on_normal_and_rom_error_exit(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        cases = {
            'normal': ('    ret\n', 0),
            'rom_error': ('    rst 8\n    db 3\n', 4),
            'rom_room': ('    ld bc,4096\n    call $1f05\n    ret\n', 4),
        }
        for label, (body, expected) in cases.items():
            with self.subTest(label=label):
                source = ('    section text\n    global start\nstart:\n' + body +
                          '    section bss\n    ds 4\n')
                text, obj, ssx = assemble_link(source, bytes(768), use_rom_font=True,
                                               rom_work_bytes=2048)
                self.assertIn('rbc_wrapper_rom_work:\n    ds 2048', text)
                self.assertIn('rbc_wrapper_rom_error_sp:', text)
                for ptr in ('5c61', '5c63', '5c65'):
                    self.assertIn('rbc_wrapper_saved_work_' + ptr, text)
                self.assertLessEqual(len(ssx), 14000)
                with tempfile.TemporaryDirectory() as tmp:
                    executable = Path(tmp) / 'rom-work-exit.ssx'
                    executable.write_bytes(ssx)
                    session = rvm.run_kernel(executable, keys='', frames=800,
                                             system=SYSTEM)
                    self.assertEqual(session.why, 'exit', session.summary())
                    self.assertEqual(session.fg.status, expected)
                    self.assertFalse(session.session.owns_screen(session.fg.pid))
                    for addr in (0x5c61, 0x5c63, 0x5c65, 0x5c3d):
                        ptr = (session.session.m.mem[addr] |
                               (session.session.m.mem[addr+1] << 8))
                        self.assertLess(ptr, 0x8000)


@unittest.skipUnless(READY, 'requires real recovered HiSoft frontend, 48K ROM and ZX-UX')
class RealExocet(unittest.TestCase):
    def test_forced_small_capacity_exits_without_kernel_panic(self):
        # In-memory test configuration, not an edited or special-cased game.
        # A 16-byte reservation cannot fit the game's 32-byte seed.
        old = native_long_string_proof.DEFAULT_CAPACITY
        try:
            native_long_string_proof.DEFAULT_CAPACITY = 16
            _, _, ssx, report = compile_native(SOURCE, CK, FE, TAPE, ROM)
        finally:
            native_long_string_proof.DEFAULT_CAPACITY = old
        self.assertEqual(report['source_proven_string_growth'][0]['max_chars'], 16)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'checked-capacity.ssx'
            path.write_bytes(ssx)
            options = rvm.Options()
            options.prog, options.keys, options.frames = str(path), '', 400
            options.system, options.cache, options.headless = str(SYSTEM), True, True
            runner = rvm.Runner(options)
            runner.start()
            panics = []
            runner.session.m.hooks[0x6048] = lambda z: panics.append(z.frame) or False
            for _ in range(400):
                runner.frame()
            runner.session.kb.type('a')
            for _ in range(1000):
                runner.frame()
                if runner.fg.ended is not None or panics:
                    break
            self.assertFalse(panics, 'kernel panic is not a bounds error handler')
            self.assertIsNotNone(runner.fg.ended)
            self.assertEqual(runner.fg.status, 3)
            self.assertFalse(runner.session.owns_screen(runner.fg.pid))
            memory = runner.session.m.mem
            self.assertLess(memory[0x5c3d] | memory[0x5c3e] << 8, 0x8000)

    def test_original_compiler_string_work_owns_private_memory(self):
        self.assertEqual(SYSTEM.read_bytes(), FROZEN.read_bytes())
        preserved = tuple(x.read_bytes() for x in (SOURCE,TZX,SSX,ROM))
        baseline = hashlib.sha256(preserved[2]).hexdigest()
        asm, obj, ssx, report = compile_native(SOURCE, CK, FE, TAPE, ROM)
        self.assertTrue(report['native_three_base_source_verified'])
        self.assertEqual(report['rom_work_bytes'], 2048)
        self.assertIn(69, report['rom_runtime_uses'])
        self.assertEqual(report['source_proven_string_growth'][0]['max_chars'], 1024)
        self.assertTrue(report['source_proven_string_growth'][0]['storage_is_reservation'])
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
            fault=[];invalid=[];panics=[]
            m.hooks[0x6048] = lambda z: panics.append(z.frame) or False
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
            self.assertFalse(panics, 'Exocet must never enter the kernel panic handler')
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
