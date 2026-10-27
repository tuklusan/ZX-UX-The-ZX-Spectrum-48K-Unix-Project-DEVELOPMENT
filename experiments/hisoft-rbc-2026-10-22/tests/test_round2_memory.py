"""Size limit must count native loader needs, not just text."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from rbc_output import memory_required


class Round2Memory(unittest.TestCase):
    def test_image_bss_stack_all_count(self):
        self.assertEqual(memory_required(dict(image=bytes(8000), bss=2000, stack=1000), 3000), 11000)

    def test_large_ssx_file_also_counts(self):
        self.assertEqual(memory_required(dict(image=b'XYZ', bss=0, stack=384), 12000), 12000)

    def test_default_is_14000(self):
        rule = (Path(__file__).resolve().parents[1] / 'stage' / 'rbc_fit.py').read_text()
        self.assertIn('default=14000', rule)
        self.assertNotIn('default=12000', rule)

    def test_size_is_exactly_reported_for_rejection(self):
        rule = (Path(__file__).resolve().parents[1] / 'stage' / 'rbc_fit.py').read_text()
        self.assertIn('memory_required(rld.parse_ssx(ssx), len(ssx))', rule)
        self.assertIn('needs %d bytes of native memory (limit %d)', rule)
        self.assertIn("if mode == 'link' and args.max and measured > args.max", rule)


if __name__ == '__main__':
    unittest.main()
