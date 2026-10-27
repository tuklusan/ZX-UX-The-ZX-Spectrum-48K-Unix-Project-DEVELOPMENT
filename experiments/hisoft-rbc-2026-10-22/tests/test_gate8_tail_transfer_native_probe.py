"""Native Z80 probe for whole-source optimizer tail transfer candidates."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path[:0] = [str(STAGE), str(ROOT / 'src/zx-ux-sdk')]
from z80_python.cpu import Z80CPU
from gate8_native_whole_optimizer import verify_whole_optimizer_candidate
import ras
import rld


BEFORE = ('    section text\n    global start\nstart:\n'
          '    call worker\n    ret\n'
          'worker:\n    ld a,42\n    ret\n')
AFTER = BEFORE.replace('    call worker\n    ret\n', '    jp worker\n')


def assemble(asm_text):
    obj = ras.assemble_text(asm_text, 'tail-source.s')
    return rld.link([rld.Obj(obj, 'tail-source.sso')], [],
                    entry='start', stack=384)[0]


def execute(ssx, base, seed):
    parsed = rld.parse_ssx(ssx)
    mem = bytearray([0xa5]) * 65536
    mem[base:base+len(parsed['image'])] = rld.relocate(
        parsed['image'], parsed['relocs'], base)
    sentinel = 0xb000
    mem[0xd000:0xd002] = sentinel.to_bytes(2, 'little')
    cpu = Z80CPU(mem.__getitem__, mem.__setitem__)
    cpu.pc = base + parsed['entry']
    cpu.sp = 0xd000
    cpu.a = seed
    cpu.f = 0xa4
    for _ in range(40):
        if cpu.pc == sentinel:
            break
        cpu.step()
    else:
        raise AssertionError('native program failed to return')
    return {'a': cpu.a, 'f': int(cpu.f), 'sp': cpu.sp,
            'stack_writes': bytes(mem[0xcffe:0xd000])}


class WholeNativeTailProbe(unittest.TestCase):
    def test_native_tail_transfer_keeps_registers_but_changes_stack_storage(self):
        before = assemble(BEFORE)
        candidate = verify_whole_optimizer_candidate(
            BEFORE, before, lambda _: AFTER)
        self.assertTrue(candidate['native_candidate_link_verified'])
        self.assertFalse(candidate['optimizer_candidate_admitted_for_publication'])
        self.assertFalse(candidate['native_behavior_verified'])
        after = assemble(AFTER)
        for base in (0x7000, 0x8000, 0x9000):
            for seed in (0, 1, 127, 255):
                with self.subTest(base=base, seed=seed):
                    original = execute(before, base, seed)
                    optimized = execute(after, base, seed)
                    for field in ('a', 'f', 'sp'):
                        self.assertEqual(original[field], optimized[field])
                    self.assertEqual(original['a'], 42)
                    self.assertNotEqual(original['stack_writes'],
                                        optimized['stack_writes'])
                    self.assertEqual(optimized['stack_writes'], b'\xa5\xa5')


if __name__ == '__main__':
    unittest.main()
