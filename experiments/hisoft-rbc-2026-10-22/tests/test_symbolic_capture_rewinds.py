"""Source-event replay proof for original HiSoft speculative rewinds."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from symbolic_capture import Capture, Emission


def emit(position, data, source, kind='instruction', symbol=None, site='producer:12'):
    return Emission(position, kind, source, data, symbol, site)


class RewindCaptureTests(unittest.TestCase):
    def trial(self):
        return [emit(0, b'\x20\x02', 'jr nz,+2'),
                emit(2, b'\xcf\x03', 'rst 8; defb 3')]

    def test_exact_replay_discards_only_prior_speculative_records(self):
        trial = self.trial()
        c = Capture(events=trial + trial)
        c.rewinds.append((0, 4, 2))
        c.canonicalize_replays(b'\x20\x02\xcf\x03')
        self.assertEqual(c.events, trial)
        self.assertEqual(c.discarded_replays, [tuple(trial)])
        self.assertEqual(c.audit(b'\x20\x02\xcf\x03')['rewritten_bytes'], 0)

    def test_partial_replacement_does_not_hide_old_source(self):
        trial = self.trial()
        c = Capture(events=trial + [trial[0]])
        c.rewinds.append((0, 4, 2))
        c.canonicalize_replays(b'\x20\x02\xcf\x03')
        self.assertEqual(c.events, trial + [trial[0]])
        self.assertEqual(c.discarded_replays, [])

    def test_changed_source_or_relocation_does_not_hide_rewrite(self):
        trial = [emit(0, b'\xc3', 'jp nn', 'opcode'),
                 emit(1, b'\x25\x12', '(nn)', 'relocation', 0x1200)]
        for replacement in (
                [emit(0, b'\xc3', 'jp nn', 'opcode'),
                 emit(1, b'\x25\x12', '(nn)', 'relocation', 0x1201)],
                [emit(0, b'\xc3', 'jump nn', 'opcode'), trial[1]],
                [emit(0, b'\xc3', 'jp nn', 'opcode', site='unknown'), trial[1]],
        ):
            with self.subTest(replacement=replacement):
                c = Capture(events=trial + replacement)
                c.rewinds.append((0, 3, 2))
                c.canonicalize_replays(b'\xc3\x25\x12')
                self.assertEqual(c.events, trial + replacement)
                self.assertEqual(c.discarded_replays, [])

    def test_replay_must_match_final_machine_image(self):
        trial = self.trial()
        c = Capture(events=trial + trial)
        c.rewinds.append((0, 4, 2))
        c.canonicalize_replays(b'\x20\x02\xcf\x04')
        self.assertEqual(c.events, trial + trial)

    def test_missing_explicit_rewind_does_not_prune_overlap(self):
        trial = self.trial()
        c = Capture(events=trial + trial)
        c.canonicalize_replays(b'\x20\x02\xcf\x03')
        self.assertEqual(c.audit(b'\x20\x02\xcf\x03')['rewritten_bytes'], 4)


if __name__ == '__main__':
    unittest.main()
