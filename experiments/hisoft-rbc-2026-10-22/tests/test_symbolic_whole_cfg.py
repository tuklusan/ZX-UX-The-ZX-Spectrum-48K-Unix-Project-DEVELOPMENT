"""Source-only control-flow regression gates for typed whole programs."""
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from symbolic_source_boundaries import SourceBoundary as Span
from symbolic_whole_cfg import WholeCFGError, inspect_whole_cfg, verify_three_whole_cfg


def assemble(source):
    source = source.lower().strip()
    if source.startswith('jr nz,'):
        return bytes((0x20, int(source.split(',')[1]) & 255))
    if source.startswith('jr '):
        return bytes((0x18, int(source[3:]) & 255))
    if source == 'djnz -2':
        return b'\x10\xfe'
    raise ValueError(source)


class FullSourceControl(unittest.TestCase):
    def test_internal_relative_branch_and_sourced_return(self):
        spans = (Span(0, 2, 'instruction', 'jr nz,+1'),
                 Span(2, 3, 'instruction', 'ret'),
                 Span(3, 4, 'instruction', 'ret'))
        flow = inspect_whole_cfg(spans, 4, assemble)
        self.assertEqual(flow.reachable, (0, 2, 3))
        self.assertEqual(flow.edges, ((0, 2), (0, 3)))
        self.assertEqual(flow.terminal_exits, 2)
        self.assertEqual(verify_three_whole_cfg((flow, flow, flow), (0x6000, 0x6100, 0x6200))
                         ['source_cfg_reachable_instructions'], 3)

    def test_explicit_extra_entry_can_reach_separate_routine(self):
        spans = (Span(0, 1, 'instruction', 'ret'),
                 Span(1, 2, 'instruction', 'ret'))
        flow = inspect_whole_cfg(spans, 2, assemble, (0, 1))
        self.assertEqual(flow.unreached, ())
        self.assertEqual(flow.entries, (0, 1))

    def test_unreached_source_code_not_falsely_marked_reachable(self):
        spans = (Span(0, 1, 'instruction', 'ret'),
                 Span(1, 2, 'instruction', 'nop'))
        self.assertEqual(inspect_whole_cfg(spans, 2, assemble).unreached, (1,))

    def test_fallthrough_into_inline_data_refused(self):
        spans = (Span(0, 1, 'instruction', 'nop'),
                 Span(1, 2, 'inline-data', 'defb 0xc9'))
        with self.assertRaisesRegex(WholeCFGError, 'enters data'):
            inspect_whole_cfg(spans, 2, assemble)

    def test_relocated_branch_into_operand_refused(self):
        spans = (Span(0, 3, 'instruction-relocated', 'jp nn', 1),
                 Span(3, 4, 'instruction', 'ret'))
        with self.assertRaisesRegex(WholeCFGError, 'enters data'):
            inspect_whole_cfg(spans, 4, assemble)

    def test_unresolved_indirect_jump_refused(self):
        spans = (Span(0, 1, 'instruction', 'jp (hl)'),)
        with self.assertRaisesRegex(WholeCFGError, 'indirect'):
            inspect_whole_cfg(spans, 1, assemble)

    def test_unknown_external_jump_refused(self):
        spans = (Span(0, 3, 'instruction', 'jp 0x6000'),)
        with self.assertRaisesRegex(WholeCFGError, 'non-symbolic'):
            inspect_whole_cfg(spans, 3, assemble)

    def test_rom_calls_fall_through_and_unconditional_rom_jump_exits(self):
        spans = (Span(0, 3, 'instruction', 'call 0x0010'),
                 Span(3, 4, 'instruction', 'ret'),
                 Span(4, 7, 'instruction', 'jp 0x0000'))
        flow = inspect_whole_cfg(spans, 7, assemble, (0, 4))
        self.assertEqual(flow.rom_transfers, 2)
        self.assertEqual(flow.reachable, (0, 3, 4))

    def test_loop_stays_bounded(self):
        spans = (Span(0, 2, 'instruction', 'djnz -2'),
                 Span(2, 3, 'instruction', 'ret'))
        flow = inspect_whole_cfg(spans, 3, assemble)
        self.assertEqual(flow.edges, ((0, 0), (0, 2)))

    def test_bad_executable_entry_and_changed_base_rejected(self):
        spans = (Span(0, 1, 'inline-data', 'defb 0xc9'),)
        with self.assertRaisesRegex(WholeCFGError, 'CFG entry'):
            inspect_whole_cfg(spans, 1, assemble)
        valid = inspect_whole_cfg((Span(0, 1, 'instruction', 'ret'),), 1, assemble)
        with self.assertRaisesRegex(WholeCFGError, 'changed'):
            verify_three_whole_cfg((valid, valid, inspect_whole_cfg(
                (Span(0, 1, 'instruction', 'ret'), Span(1, 2, 'instruction', 'ret')),
                2, assemble, (0, 1))), (0x6000, 0x6100, 0x6200))


if __name__ == '__main__':
    unittest.main()
