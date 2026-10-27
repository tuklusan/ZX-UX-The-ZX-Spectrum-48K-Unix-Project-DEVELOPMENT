"""Native Z80 proof: removing a save-load changes system variable restoration."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]

from z80_python.cpu import Z80CPU
import ras
import rld
from gate8_native_whole_optimizer import (
    WholeOptimizerError, verify_whole_optimizer_candidate)


ORIGINAL = (
    '    section text\n    global start\nstart:\n'
    '    ld a,(23692)\n    push af\n    ld a,255\n'
    '    ld (23692),a\n    pop af\n    ld (23692),a\n    ret\n')
CANDIDATE = ORIGINAL.replace('    ld a,(23692)\n', '')


def native_link(source):
    obj = ras.assemble_text(source, 'scrct-restoration.s')
    return rld.link([rld.Obj(obj, 'scrct-restoration.sso')], [],
                    entry='start', stack=384)[0]


def run_native(ssx, base, initial_a, scr_ct):
    parsed = rld.parse_ssx(ssx)
    memory = bytearray([0xa5]) * 65536
    memory[base:base + len(parsed['image'])] = rld.relocate(
        parsed['image'], parsed['relocs'], base)
    memory[23692] = scr_ct
    memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
    cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
    cpu.pc = base + parsed['entry']
    cpu.sp = 0xd000
    cpu.a = initial_a
    cpu.f = 0x34
    for _ in range(30):
        if cpu.pc == 0xb000:
            break
        cpu.step()
    else:
        raise AssertionError('native return not reached')
    return memory[23692], cpu.a, int(cpu.f), cpu.sp


class SysvarRestorationTests(unittest.TestCase):
    def test_native_memory_and_register_effects_disagree_after_deleted_read(self):
        before = native_link(ORIGINAL)
        after = native_link(CANDIDATE)
        with self.assertRaisesRegex(WholeOptimizerError,
                                    'memory, I/O or stack effects'):
            verify_whole_optimizer_candidate(ORIGINAL, before,
                                             lambda _: CANDIDATE)
        for base in (0x7000, 0x8000, 0x9000):
            for scr_ct, seed in ((0x11, 0x44), (0xfe, 0x01)):
                with self.subTest(base=base, scr_ct=scr_ct, seed=seed):
                    original = run_native(before, base, seed, scr_ct)
                    changed = run_native(after, base, seed, scr_ct)
                    self.assertEqual(original[:2], (scr_ct, scr_ct))
                    self.assertEqual(changed[:2], (seed, seed))
                    self.assertEqual(original[2:], changed[2:])
                    self.assertNotEqual(original, changed)


if __name__ == '__main__':
    unittest.main()
