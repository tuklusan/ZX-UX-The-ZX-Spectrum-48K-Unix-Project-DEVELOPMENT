"""48K ULA keyboard and idle EAR read checks."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'zx-ux-sdk'))
from zxmachine import Machine


class UlaEarTests(unittest.TestCase):
    def test_issue_3_idle_reads_last_speaker_bit(self):
        m = Machine(ula_issue=3)
        m.press({'x'})
        self.assertEqual(m._in(0xFEFE), 0xBB)
        m._out(0x00FE, 0x10)
        self.assertEqual(m._in(0xFEFE), 0xFB)
        m._out(0x00FE, 0x08)  # MIC alone is low on Issue 3
        self.assertEqual(m._in(0xFEFE), 0xBB)
        m._out(0x00FE, 0x18)
        self.assertEqual(m._in(0xFEFE), 0xFB)

    def test_issue_2_mic_feedback(self):
        m = Machine(ula_issue=2)
        m.press({'x'})
        m._out(0x00FE, 0x08)
        self.assertEqual(m._in(0xFEFE), 0xFB)
        m._out(0x00FE, 0x00)
        self.assertEqual(m._in(0xFEFE), 0xBB)

    def test_both_keys_match_original_game_values(self):
        m = Machine()
        m._out(0x00FE, 0x10)
        for key, expected in [('x', 251), ('z', 253)]:
            with self.subTest(key=key):
                m.press({key})
                self.assertEqual(m._in(65278), expected)
        m.press(set())
        self.assertEqual(m._in(65278), 255)

    def test_cassette_edges_still_take_priority(self):
        m = Machine()
        m._out(0x00FE, 0x10)
        m.press({'x'})
        m.pulses = [100, 200]
        m.tnow = 50
        self.assertEqual(m._in(65278), 0xBB)
        m.tnow = 150
        self.assertEqual(m._in(65278), 0xFB)
        m.tnow = 250
        self.assertEqual(m._in(65278), 0xBB)

    def test_other_ports_and_invalid_issue(self):
        m = Machine()
        m._out(0x00FE, 0x10)
        self.assertEqual(m._in(0xFFFF), 255)
        with self.assertRaises(ValueError):
            Machine(ula_issue=4)


if __name__ == '__main__':
    unittest.main()
