"""Verify Galaxians port values using the native ZX-UX ULA model."""
import sys
import unittest
from pathlib import Path

repo = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo / 'dist/sdk/bin/py'))
from zxmachine import Machine


class KeyboardULATests(unittest.TestCase):
    def test_issue_3_native_keyboard_values(self):
        m = Machine(ula_issue=3)
        self.assertEqual(m.cpu.read_port(65278), 191)
        # The normal MIC/EAR output state drives the idle input bit.
        m._out(0x00FE, 0x10)
        self.assertEqual(m.cpu.read_port(65278), 255)
        for key, port, expected in (
            ('z', 65278, 253), ('x', 65278, 251), ('m', 32766, 251)
        ):
            with self.subTest(key=key):
                m.press({key})
                self.assertEqual(m.cpu.read_port(port), expected)
        m.press(set())
        self.assertEqual(m.cpu.read_port(65278), 255)
        m._out(0x00FE, 0x08)
        self.assertEqual(m.cpu.read_port(65278), 191)

    def test_issue_2_mic_audio_feedback(self):
        m = Machine(ula_issue=2)
        m._out(0x00FE, 0x08)
        m.press({'x'})
        self.assertEqual(m.cpu.read_port(65278), 251)
        m._out(0x00FE, 0x00)
        self.assertEqual(m.cpu.read_port(65278), 187)

    def test_tape_pulses_override_idle_audio_state(self):
        m = Machine()
        m._out(0x00FE, 0x10)
        m.press({'x'})
        m.pulses = [1000, 2000, 3000]
        for t, expected in ((500, 187), (1500, 251), (2500, 187)):
            with self.subTest(t=t):
                m.tnow = t
                self.assertEqual(m.cpu.read_port(65278), expected)
        self.assertEqual(m.cpu.read_port(65279), 255)

    def test_reject_invalid_ula_issue(self):
        with self.assertRaises(ValueError):
            Machine(ula_issue=4)


if __name__ == '__main__':
    unittest.main()
