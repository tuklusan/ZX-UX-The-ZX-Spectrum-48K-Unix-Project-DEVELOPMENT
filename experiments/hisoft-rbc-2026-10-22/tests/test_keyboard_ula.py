"""Check Spectrum hardware keyboard values used by the original games."""
import sys
import unittest
from pathlib import Path

experiment = Path(__file__).resolve().parents[1]
repo = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(experiment / 'stage'))
sys.path.insert(0, str(repo / 'dist/sdk/bin/py'))
from keyboard_ula import idle_ear_high


class KeyboardULATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import zxmachine
        cls.machine_type = zxmachine.Machine

    def test_galaxians_ports_and_restoration(self):
        machine = self.machine_type()
        self.assertEqual(machine.cpu.read_port(65278), 0xBF)
        restore = idle_ear_high(machine)
        try:
            self.assertEqual(machine.cpu.read_port(65278), 255)
            machine.press(('z',))
            self.assertEqual(machine.cpu.read_port(65278), 253)
            machine.press(('x',))
            self.assertEqual(machine.cpu.read_port(65278), 251)
            machine.press(('m',))
            self.assertEqual(machine.cpu.read_port(32766), 251)
        finally:
            restore()
        self.assertEqual(machine.cpu.read_port(65278), 191)

    def test_odd_port_and_tape_pulses_unchanged(self):
        machine = self.machine_type()
        original = machine.cpu.read_port
        machine.pulses = [1000, 2000, 3000]
        machine.tnow = 1500
        old_value = original(65278)
        restore = idle_ear_high(machine)
        self.assertEqual(machine.cpu.read_port(65278), old_value)
        self.assertEqual(machine.cpu.read_port(65279), original(65279))
        restore()


if __name__ == '__main__':
    unittest.main()
