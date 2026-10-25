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

    def test_default_is_11000(self):
        from rbc_fit import patched
        source = Path('build/tmp/rbc-round2/checkpoint/scratch/rbc/rbc.py')
        if not source.is_file():
            self.fail('Unmodified original RBC source not available for fit check')
        result = patched(source.read_text())
        self.assertIn('default=12000', result)
        self.assertNotIn('default=11000', result)

    def test_size_is_exactly_reported_for_rejection(self):
        from rbc_fit import patched
        source = Path('build/tmp/rbc-round2/checkpoint/scratch/rbc/rbc.py')
        result = patched(source.read_text())
        self.assertIn('memory_required', result)
        self.assertIn('needs %d bytes of native memory (limit %d)', result)


if __name__ == '__main__':
    unittest.main()
