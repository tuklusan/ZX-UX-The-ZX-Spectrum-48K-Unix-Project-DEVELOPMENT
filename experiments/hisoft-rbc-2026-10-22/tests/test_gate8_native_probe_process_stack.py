"""Bounded Z80 probes must place stack writes inside the admitted process."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import _run, compare_native_probes


def native_stack_program(stack=8, bss=0):
    source = ('    section text\n    global start\nstart:\n'
              '    push hl\n    pop hl\n    ret\n'
              '    section bss\n    defs ' + str(bss) + '\n')
    obj = ras.assemble_text(source, 'native-stack-region.s')
    return rld.link([rld.Obj(obj, 'native-stack-region.sso')], [],
                    entry='start', stack=stack)[0]


class ProcessStackPlacement(unittest.TestCase):
    def test_stack_writes_live_in_declared_region_at_each_base(self):
        native = native_stack_program(stack=8, bss=12)
        parsed = rld.parse_ssx(native)
        for base in (0x6000, 0x7000, 0x8000):
            with self.subTest(base=base):
                process_end = base + len(parsed['image']) + parsed['bss'] + parsed['stack']
                state, tstates, writes, ports = _run(native, base, 0, 16)
                self.assertEqual([pos for pos, _ in writes],
                                 [process_end - 1, process_end - 2])
                self.assertEqual(state.sp, process_end + 2)
                self.assertEqual(state.pc, 0xb000)
                self.assertGreater(tstates, 0)
                self.assertEqual(ports, ())

    def test_stack_relocation_normalized_after_dead_code_size_reduction(self):
        def link(code):
            obj = ras.assemble_text(code, 'native-stack-dead-code.s')
            return rld.link([rld.Obj(obj, 'native-stack-dead-code.sso')], [],
                            entry='start', stack=16)[0]
        start = ('    section text\n    global start\nstart:\n'
                 '    jp reached\n    nop\nreached:\n'
                 '    push hl\n    pop hl\n    ret\n')
        reduced = start.replace('    nop\n', '')
        original = link(start)
        candidate = link(reduced)
        self.assertEqual(len(rld.parse_ssx(original)['image']),
                         len(rld.parse_ssx(candidate)['image']) + 1)
        # Both programs execute identical instructions; only process layout
        # moves the initial stack and its two PUSH writes by one byte.
        report = compare_native_probes(original, candidate)
        self.assertEqual(report['checked_exits'], 12)
        self.assertTrue(report['bounded_exit_states_match'])
        self.assertFalse(report['native_behavior_verified'])
        self.assertNotEqual(_run(original, 0x6000, 0, 32)[2],
                            _run(candidate, 0x6000, 0, 32)[2])

    def test_two_candidates_still_match_at_relocated_stack_addresses(self):
        native = native_stack_program(stack=8, bss=12)
        match = compare_native_probes(native, native)
        self.assertEqual(match['checked_exits'], 12)
        self.assertTrue(match['bounded_exit_states_match'])
        self.assertFalse(match['native_behavior_verified'])


if __name__ == '__main__':
    unittest.main()
