"""Full Spectrum system-variable access must be isolated to a process."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))


class Round2SystemVariables(unittest.TestCase):
    def system(self):
        from spectrum_sysvars import ProcessSystemVariables
        return ProcessSystemVariables()

    def test_caps_lock_flags2_read_write(self):
        state = self.system()
        state.poke(23658, 0x55)
        self.assertEqual(state.peek(23658), 0x55)

    def test_pip_click_read_write(self):
        state = self.system()
        state.poke(23609, 0x23)
        self.assertEqual(state.peek(23609), 0x23)

    def test_frames_three_bytes_and_rollover(self):
        state = self.system()
        for address in (23672, 23673, 23674):
            state.poke(address, 255)
        state.tick()
        self.assertEqual([state.peek(a) for a in (23672, 23673, 23674)], [0, 0, 0])

    def test_frames_middle_byte_carries(self):
        state = self.system()
        state.poke(23672, 255)
        state.poke(23673, 12)
        state.poke(23674, 4)
        state.tick()
        self.assertEqual([state.peek(a) for a in (23672, 23673, 23674)], [0, 13, 4])

    def test_processes_do_not_share_system_memory(self):
        first, second = self.system(), self.system()
        first.poke(23658, 255)
        first.poke(23609, 12)
        self.assertNotEqual(second.peek(23658), 255)
        self.assertNotEqual(second.peek(23609), 12)


if __name__ == '__main__':
    unittest.main()
