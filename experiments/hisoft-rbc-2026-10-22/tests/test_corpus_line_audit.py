"""Test the shared tape reader used by RBC against an untouched original tape."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'experiments/hisoft-rbc-2026-10-22'))
from corpus_line_audit import basic_lines, tape_blocks  # noqa: E402


class TapeReaderTests(unittest.TestCase):
    def test_basic_variables_are_not_source_lines(self):
        path = ROOT / 'src/bonus/60-programs/01-minelay/BASIC/01-minelay.tzx'
        blocks = tape_blocks(path.read_bytes())
        header = next(block for block in blocks if len(block) == 19 and block[:2] == b'\x00\x00')
        variables_at = int.from_bytes(header[16:18], 'little')
        total = int.from_bytes(header[12:14], 'little')
        self.assertEqual(total, 4635)
        self.assertEqual(variables_at, 4597)
        self.assertEqual(total - variables_at, 38)
        rows = basic_lines(path.read_bytes())
        self.assertEqual(len(rows), 81)
        self.assertEqual(sum(len(body) + 4 for body in rows.values()), variables_at)
        self.assertEqual(max(rows), 9999)


if __name__ == '__main__':
    unittest.main()
