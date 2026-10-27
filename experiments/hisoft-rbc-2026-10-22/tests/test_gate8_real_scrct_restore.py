"""Native probe of SCR_CT restoration in an authentic whole-source RBC build.

This runs source-derived instruction sequences, not complete gameplay. A ROM
print RST is stubbed with RET so each isolated sequence can be measured.
Neither original BASIC/tape nor native output files are modified or published.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

import ras
import rld
from z80_python.cpu import Z80CPU
from gate8_native_whole_optimizer import load_locked_optimizer

# These instructions are copied from the native *source*, using the real Z80
# assembler to derive bytes. We do not patch a linked game to fit a test.
_SAVE = ('ld a,(23692);push af;ld a,255;ld (23692),a;'
         'ld a,13;rst $10;pop af;ld (23692),a')
_DROPPED_READ = ('push af;ld a,255;ld (23692),a;'
                 'ld a,13;rst $10;pop af;ld (23692),a')


def _native_link(source: str) -> bytes:
    obj = ras.assemble_text(source, 'gate8-scrct-original-source.s')
    return rld.link([rld.Obj(obj, 'gate8-scrct-original-source.sso')], [],
                    entry='start', stack=384)[0]


def _locations(image: bytes, needle: bytes) -> tuple[int, ...]:
    return tuple(i for i in range(len(image)) if image.startswith(needle, i))


def _isolated_native_span(ssx: bytes, base: int, offset: int, code: bytes,
                          initial_a: int, initial_scr_ct: int) -> tuple:
    info = rld.parse_ssx(ssx)
    image = bytes(rld.relocate(info['image'], info['relocs'], base))
    assert image[offset:offset + len(code)] == code
    memory = bytearray(b'\xa5') * 65536
    memory[0x10] = 0xc9  # Stand-in ROM RST $10: return to the caller.
    memory[base:base + len(image)] = image
    memory[23692] = initial_scr_ct
    cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
    cpu.pc = base + offset
    cpu.sp = 0xd000
    cpu.a = initial_a
    cpu.f = 0x34
    ending_pc = base + offset + len(code)
    for _ in range(24):
        if cpu.pc == ending_pc:
            break
        cpu.step()
    else:
        raise AssertionError('source-owned native SCR_CT sequence did not finish')
    return (memory[23692], cpu.a, int(cpu.f), cpu.sp,
            bytes(memory[0xcffe:0xd000]))


class RealCompilerScrctTests(unittest.TestCase):
    def test_hisoft_rbc_save_restore_survives_original_not_optimizer(self):
        required = tuple(os.environ.get(name) for name in (
            'RBC_G8_CHECKPOINT', 'RBC_G8_FRONTEND', 'RBC_G8_TAPE',
            'RBC_G8_OPTIMIZER'))
        if not all(required):
            self.skipTest('exact upstream compiler and optimizer needed')
        from z80asm import asm
        from gate8_full_source_audit import run
        import gate8_whole_native_baseline as native_baseline

        original_assembler = native_baseline.ras.assemble_text
        captured = []

        def witness(source, name):
            if name == 'rbc-whole-source-baseline.s':
                captured.append(source)
            return original_assembler(source, name)

        game = '23-biorhythms'
        original_bas = (ROOT / 'src/bonus/60-programs' / game /
                        'BASIC' / (game + '.bas'))
        before_input = hashlib.sha256(original_bas.read_bytes()).hexdigest()
        with patch.object(native_baseline.ras, 'assemble_text', side_effect=witness):
            report = run(original_bas, Path(required[0]), Path(required[1]),
                         Path(required[2]), ROOT / 'src/zx-ux-sdk/rom/48.rom')
        self.assertEqual(before_input,
                         hashlib.sha256(original_bas.read_bytes()).hexdigest())
        self.assertEqual(len(captured), 3)
        self.assertEqual(len(set(captured)), 1)
        baseline_report = report['native_whole_source_baseline']
        self.assertTrue(baseline_report['native_whole_source_baseline_linked'])
        self.assertTrue(baseline_report['native_image_byte_exact'])
        self.assertFalse(report['gate8_complete'])
        self.assertIn('protected resource boundary',
                      baseline_report['native_whole_optimizer_candidate']['blocker'])

        baseline_ssx = _native_link(captured[0])
        self.assertEqual(hashlib.sha256(baseline_ssx).hexdigest(),
                         baseline_report['native_sha256'])
        optimizer = load_locked_optimizer(Path(required[3]))
        rejected_source = optimizer.optimize(captured[0])
        rejected_ssx = _native_link(rejected_source)
        self.assertNotEqual(rejected_ssx, baseline_ssx)
        original_code = asm(_SAVE)
        rejected_code = asm(_DROPPED_READ)
        original_image = rld.parse_ssx(baseline_ssx)['image']
        rejected_image = rld.parse_ssx(rejected_ssx)['image']
        first = _locations(original_image, original_code)
        second = _locations(rejected_image, rejected_code)
        self.assertEqual(len(first), 9)
        self.assertEqual(len(second), 9)
        for base in (0x7000, 0x8000, 0x9000):
            for scr_ct, a in ((0x11, 0x44), (0xfe, 0x01)):
                for index, (a_offset, b_offset) in enumerate(zip(first, second)):
                    with self.subTest(base=base, instance=index,
                                      scr_ct=scr_ct, initial_a=a):
                        good = _isolated_native_span(
                            baseline_ssx, base, a_offset, original_code, a, scr_ct)
                        bad = _isolated_native_span(
                            rejected_ssx, base, b_offset, rejected_code, a, scr_ct)
                        self.assertEqual(good[:4], (scr_ct, scr_ct, 0x34, 0xd000))
                        self.assertEqual(bad[:4], (a, a, 0x34, 0xd000))
                        self.assertNotEqual(good, bad)


if __name__ == '__main__':
    unittest.main()
