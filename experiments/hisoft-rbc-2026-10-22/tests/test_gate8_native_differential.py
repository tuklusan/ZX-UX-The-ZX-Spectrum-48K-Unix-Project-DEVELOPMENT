"""Independent native-link and Z80 probes for optimizer candidate safety."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import (NativeProbeBlocked,
                                       compare_native_probes)


def link(instructions):
    source = ('    section text\n    global start\nstart:\n' +
              ''.join('    ' + ins + '\n' for ins in instructions))
    obj = ras.assemble_text(source, 'native-diff.s')
    return rld.link([rld.Obj(obj, 'native-diff.sso')], [],
                    entry='start', stack=384)[0]


class NativeDifferential(unittest.TestCase):
    def test_identical_linked_native_programs_agree_at_three_bases(self):
        native = link(('ld a,25', 'ld (23692),a', 'ret'))
        result = compare_native_probes(native, native)
        self.assertEqual(result['checked_exits'], 12)
        self.assertTrue(result['bounded_exit_states_match'])
        self.assertEqual(result['first_mismatches'], [])
        self.assertFalse(result['native_behavior_verified'])

    def test_shorter_arithmetic_instruction_changes_flags_and_clock(self):
        before = link(('ld a,0', 'ret'))
        candidate = link(('xor a', 'ret'))
        result = compare_native_probes(before, candidate)
        self.assertEqual(result['checked_exits'], 12)
        self.assertFalse(result['bounded_exit_states_match'])
        self.assertTrue(all('processor_state' in x['changed'] and
                            't_states' in x['changed']
                            for x in result['first_mismatches']))
        self.assertFalse(result['native_behavior_verified'])

    def test_removed_register_noop_changes_refresh_and_clock(self):
        before = link(('ld a,a', 'ret'))
        candidate = link(('ret',))
        result = compare_native_probes(before, candidate)
        self.assertFalse(result['bounded_exit_states_match'])
        self.assertIn('processor_state', result['first_mismatches'][0]['changed'])
        self.assertIn('t_states', result['first_mismatches'][0]['changed'])

    def test_different_memory_writes_are_detected(self):
        before = link(('ld a,25', 'ld (23692),a', 'ret'))
        candidate = link(('ld a,26', 'ld (23692),a', 'ret'))
        result = compare_native_probes(before, candidate)
        self.assertIn('memory_writes', result['first_mismatches'][0]['changed'])

    def test_escaped_rom_or_unsupported_execution_fails_closed(self):
        rom = link(('jp 56',))
        loop = link(('jr start',))
        with self.assertRaisesRegex(NativeProbeBlocked, 'escaped'):
            compare_native_probes(rom, rom)
        with self.assertRaisesRegex(NativeProbeBlocked, 'did not return'):
            compare_native_probes(loop, loop, limit=16)

    def test_exact_one_instruction_budget_allows_a_real_return(self):
        native = link(('ret',))
        result = compare_native_probes(native, native, limit=1)
        self.assertEqual(result['checked_exits'], 12)
        self.assertTrue(result['bounded_exit_states_match'])

    def test_spoofed_caller_stack_pointer_without_return_is_rejected(self):
        spoof = link(('ld sp,53250', 'jp 45056'))
        with self.assertRaisesRegex(NativeProbeBlocked, 'caller stack'):
            compare_native_probes(spoof, spoof)

    def test_real_conditional_return_to_caller_is_accepted(self):
        source = link(('ret z', 'ret'))
        result = compare_native_probes(source, source)
        self.assertEqual(result['checked_exits'], 12)
        self.assertTrue(result['bounded_exit_states_match'])

    def test_invalid_native_location_or_arguments_are_rejected(self):
        native = link(('ret',))
        with self.assertRaisesRegex(NativeProbeBlocked, 'outside bounded'):
            compare_native_probes(native, native, bases=(0xf000,))
        with self.assertRaisesRegex(NativeProbeBlocked, 'invalid initial'):
            compare_native_probes(native, native, flags=(256,))
        with self.assertRaisesRegex(NativeProbeBlocked, 'invalid bounded'):
            compare_native_probes(native, native, limit=0)

    def test_exiting_without_stack_return_fails_closed(self):
        jump = link(('jp 45056',))
        with self.assertRaisesRegex(NativeProbeBlocked, 'caller stack'):
            compare_native_probes(jump, jump)


if __name__ == '__main__':
    unittest.main()
