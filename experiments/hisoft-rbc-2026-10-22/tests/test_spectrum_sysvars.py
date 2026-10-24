"""Process-owned ZX Spectrum variable model, independent of shell memory."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from spectrum_sysvars import ProcessSystemVariables, FLAGS2, PIP, FRAMES

class SystemVariableModel(unittest.TestCase):
    def test_bytes_are_isolated(self):
        a, b = ProcessSystemVariables(), ProcessSystemVariables()
        a.poke(FLAGS2, 0xff); a.poke(PIP, 128)
        self.assertEqual((a.peek(FLAGS2), a.peek(PIP)), (255, 128))
        self.assertEqual((b.peek(FLAGS2), b.peek(PIP)), (0, 0))

    def test_bit_exact_split_and_join(self):
        s = ProcessSystemVariables(frames=0x5a3c7e)
        self.assertEqual([s.peek(a) for a in FRAMES], [0x7e, 0x3c, 0x5a])
        s.poke(FRAMES[1], 0x99)
        self.assertEqual(s.frames, 0x5a997e)

    def test_rollover(self):
        s = ProcessSystemVariables(frames=0xfffffe)
        self.assertEqual(s.tick(1), 0xffffff)
        self.assertEqual(s.tick(1), 0)
        self.assertEqual(s.tick(65536), 65536)

    def test_low_byte_value(self):
        s = ProcessSystemVariables()
        s.poke(PIP, 0x123); self.assertEqual(s.peek(PIP), 0x23)
        s.poke(PIP, -1); self.assertEqual(s.peek(PIP), 255)

    def test_kernel_clock_wrap_and_preserved_manual_pokes(self):
        s = ProcessSystemVariables()
        self.assertEqual(s.sync(65534), 0)
        s.poke(FRAMES[0], 0xfd)
        self.assertEqual(s.sync(1), 0x100)
        self.assertEqual(s.sync(2), 0x101)

    def test_unknown_private_memory_is_not_authorized(self):
        s = ProcessSystemVariables()
        with self.assertRaises(ValueError): s.poke(23606, 18)
        with self.assertRaises(ValueError): s.peek(0x6003)
        with self.assertRaises(ValueError): s.sync(1 << 17)
        with self.assertRaises(ValueError): s.tick(-1)

if __name__ == '__main__':
    unittest.main()
