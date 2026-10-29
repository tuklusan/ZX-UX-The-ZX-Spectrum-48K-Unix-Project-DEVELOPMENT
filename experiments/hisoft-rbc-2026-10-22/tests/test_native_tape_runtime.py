"""Tape calls fail only if reached; no tape I/O or protected writes occur.

Uses original 48K ROM syntax checks and the unchanged HiSoft source pipeline.
Actual ZX-UX loader execution is a separate gate, not implied by this CPU test.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
from tape_policy import find_tape_operations, allow_deferred_tape_traps
from native_tape_trap import TAPE_STATUS, _skip_to_statement_end, TOKENS
from native_error_exit import error_exit_bytes
from native_rbc_cli import compile_native
from rom_syntax import _ready
from z80_python.cpu import Z80CPU
import rld

FRONTEND = Path(os.getenv('RBC_FRONTEND_DIR', '/no-frontend'))
CHECKPOINT = Path(os.getenv('RBC_COMPILER_DIR', '/no-compiler'))
TAPE = Path(os.getenv('RBC_HISOFT_TAPE', '/no-tape'))
ROM = ROOT / 'src/zx-ux-sdk/rom/48.rom'
READY = all(p.is_file() for p in (FRONTEND/'compiler.py', CHECKPOINT/'rbc.py',
                                  CHECKPOINT/'font32.bin', TAPE, ROM))
NAMES = {0xef: 'LOAD', 0xf8: 'SAVE', 0xd5: 'MERGE', 0xd6: 'VERIFY'}


class Policy(unittest.TestCase):
    def test_only_real_tape_tokens_deferred(self):
        lines = [(10, b'"'+bytes(NAMES)+b'":\xea '+bytes(NAMES)),
                 (20, b'\xe4 "SAVE:LOAD", 3'),
                 (30, b'\xef "a:b":\xf8 "c"\r'),
                 (40, b'\xf5 1\x0e\xef\xf8\xd5\xd6\x00:\xd5 "c"\r')]
        self.assertEqual(find_tape_operations(lines, NAMES),
                         ((30, 'LOAD'), (30, 'SAVE'), (40, 'MERGE')))
        from dataclasses import dataclass
        @dataclass
        class Finding:
            line: int
            operation: str
            severity: str = 'block'
            classification: str = 'tape_or_external_io'
        findings = [Finding(30, 'LOAD'), Finding(30, 'SAVE'),
                    Finding(40, 'MERGE'), Finding(90, 'POKE',
                    classification='global_memory_write')]
        allow_deferred_tape_traps(lines, NAMES, findings)
        self.assertTrue(all(f.severity == 'info' for f in findings[:3]))
        self.assertEqual(findings[3].severity, 'block')

    def test_quote_and_numeric_cache_statement_walker(self):
        class Compiler:
            buf = b' "a:b" CODE 10\x0e\xef\xf8\xd5\xd6\x00:PRINT 1\r'
            ch = 0
        c = Compiler()
        _skip_to_statement_end(c)
        self.assertEqual(c.buf[c.ch:], b':PRINT 1\r')
        self.assertEqual(TOKENS, (0xef, 0xf8, 0xd5, 0xd6))


@unittest.skipUnless(READY, 'requires recovered checked HiSoft compiler and original 48K tape')
class RealNative(unittest.TestCase):
    def native_run(self, ssx, expected):
        info = rld.parse_ssx(ssx)
        base = 0x8000
        image = bytearray(info['image'])
        for at in info['relocs']:
            off = int.from_bytes(image[at:at+2], 'little')
            image[at:at+2] = (base+off).to_bytes(2, 'little')
        memory = bytearray(_ready(ROM.read_bytes()))
        memory[base:base+len(image)] = image
        preserved = {0x5c36:0x00,0x5c37:0x3c,0x5c7b:0x00,0x5c7c:0xfc,
                     0x5c6a:0xbb,0x5c39:0x34,0x5c8d:0x48,
                     0x5c8e:0x72,0x5c8f:0x4d,0x5c90:0x16}
        for address, value in preserved.items():
            memory[address] = value
        memory[0xfc00] = 0x5a
        cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
        cpu.pc = base+info['entry']
        cpu.sp = 0xe000
        cpu.iy = 0x5c3a
        calls = []
        for _ in range(100000):
            if cpu.pc == 0x6003:
                code, argument = cpu.a, cpu.h << 8 | cpu.l
                calls.append((code, argument))
                if code == 1:
                    self.assertEqual(argument, expected)
                    break
                self.assertEqual(code, 39)
                cpu.pc = memory[cpu.sp] | memory[cpu.sp+1] << 8
                cpu.sp = (cpu.sp+2)&65535
                continue
            self.assertNotEqual(cpu.pc, 8, 'unexpected ROM panic')
            cpu.step()
        else:
            self.fail('native tape fixture never returned to shell')
        self.assertEqual(calls, [(39,1),(39,0),(1,expected)])
        self.assertEqual({a:memory[a] for a in preserved}, preserved)
        self.assertEqual(memory[0xfc00], 0x5a)

    def test_all_tape_ops_only_error_when_taken(self):
        # Every source file undergoes its own strict ROM syntax check,
        # triple HiSoft compilation, typed source audit and native ras/rld link.
        work = ROOT / 'build/tmp/rbc-round2'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as temp:
            for target in (20,30,40,45,50):
                with self.subTest(tape_line=target):
                    source = Path(temp)/'source.bas'
                    source.write_text(f'''10 GO TO {target}\n20 LOAD "NEXT"\n30 SAVE "NEXT" CODE 40000,100\n40 MERGE "NEXT"\n45 VERIFY "NEXT"\n50 STOP\n''',encoding='ascii')
                    _, _, ssx, report = compile_native(
                        source, CHECKPOINT, FRONTEND, TAPE, ROM,
                        input_backend='rom', maximum=14000)
                    self.assertEqual(ssx[:4], b'SSX1')
                    self.assertTrue(report['native_three_base_source_verified'])
                    self.assertFalse(report['optimizer_used'])
                    self.assertEqual(rld.parse_ssx(ssx)['image'].count(
                        error_exit_bytes(TAPE_STATUS)), 4)
                    self.native_run(ssx, 0 if target == 50 else TAPE_STATUS)

if __name__ == '__main__':
    unittest.main()
