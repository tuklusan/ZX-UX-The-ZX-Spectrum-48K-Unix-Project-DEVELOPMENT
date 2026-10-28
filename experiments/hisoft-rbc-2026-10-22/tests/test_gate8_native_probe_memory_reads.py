"""Changed external-RAM read dependencies cannot masquerade as equivalent exits."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from gate8_native_differential import compare_native_probes


def native(instructions):
    source = ('    section text\n    global start\nstart:\n'
              + ''.join((op if op.endswith(':') else '    ' + op) + '\n' for op in instructions))
    obj = ras.assemble_text(source, 'native-read-trace.s')
    return rld.link([rld.Obj(obj, 'native-read-trace.sso')], [],
                    entry='start', stack=384)[0]


class ExternalMemoryDependencies(unittest.TestCase):
    def test_two_distinct_zero_filled_sysvars_are_not_equivalent(self):
        before = native(('ld a,(23692)', 'ret'))
        after = native(('ld a,(23693)', 'ret'))
        result = compare_native_probes(before, after)
        self.assertFalse(result['bounded_exit_states_match'])
        self.assertIn('external_memory_reads',
                      result['first_mismatches'][0]['changed'])
        self.assertNotIn('processor_state',
                         result['first_mismatches'][0]['changed'])
        self.assertNotIn('t_states',
                         result['first_mismatches'][0]['changed'])

    def test_same_ram_reads_match_across_all_bases(self):
        original = native(('ld a,(23692)', 'ld hl,(23693)', 'ret'))
        result = compare_native_probes(original, original)
        self.assertTrue(result['bounded_exit_states_match'])
        self.assertEqual(result['checked_exits'], 12)

    def test_private_stack_reads_are_compared_relative_to_own_extent(self):
        original = native(('push hl', 'pop hl', 'ret'))
        # A different sized image moves the native stack; closed-graph code
        # deletions can make this a legitimate loader relocation.
        changed = native(('jp live', 'nop', 'live:', 'push hl', 'pop hl', 'ret'))
        # Both paths have different fetched instructions/timing, so this
        # must still fail state/time comparison without a false memory-read
        # discrepancy caused solely by the relocated guest stack.
        result = compare_native_probes(original, changed)
        self.assertFalse(result['bounded_exit_states_match'])
        self.assertNotIn('external_memory_reads',
                         result['first_mismatches'][0]['changed'])


if __name__ == '__main__':
    unittest.main()
