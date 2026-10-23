"""Tests for the single approved, process-owned Scuba font mapping."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from scuba_charset import _ORIGINAL, _ADAPTED, _shape, adapt_scuba_charset, allow_scuba_font_access, rom_font


class FakeKeywords:
    TOKEN = {0xEA: 'REM', 0xFE: 'RETURN'}
    CODE_FOR = {'REM': 0xEA, 'RETURN': 0xFE}


class FakeSource:
    @staticmethod
    def tokenize_line(text, keywords):
        return text.encode('ascii')
    @staticmethod
    def hide_numbers(body, fp):
        return body


class FakeTape:
    @staticmethod
    def split_lines(rows):
        return rows
    @staticmethod
    def join_lines(rows):
        return rows


def archive_rows():
    return [(n, v.encode('ascii') + b'\r') for n, v in sorted(_ORIGINAL.items())]


class ScubaTests(unittest.TestCase):
    def test_original_keyword_boundary_before_rem(self):
        # The actual archived listing has a colon immediately before REM.
        root = Path(__file__).resolve().parents[3]
        source = root / 'src/bonus/60-programs/14-scuba/BASIC/14-scuba.bas'
        lines = source.read_text(encoding='utf-8-sig').splitlines()
        line5 = next(line for line in lines if line.startswith('5 '))
        self.assertIn('POKE 23658,255:REM', line5)
        self.assertEqual(_ORIGINAL[5], 'POKE23658,255:')

    def test_rejects_unrelated_or_changed_programs(self):
        rows = archive_rows()
        self.assertTrue(_shape(rows, FakeKeywords.TOKEN, False))
        for line, change in [(9020, b'FORX=1TO65535:POKE60000+X,0\r'),
                             (3270, b'POKE23606,96:POKE23607,200:RETURN\r'),
                             (5008, b'READA:POKE60256+(K+33)*8+J,255:NEXTJ:NEXTK\r')]:
            changed = [(n, change if n == line else body) for n, body in rows]
            self.assertFalse(_shape(changed, FakeKeywords.TOKEN, False))
            self.assertEqual(adapt_scuba_charset(changed, FakeKeywords, None, FakeSource, FakeTape),
                             (changed, []))

    def test_rewrites_only_six_compiler_lines(self):
        rows = archive_rows()
        adapted, details = adapt_scuba_charset(rows, FakeKeywords, None, FakeSource, FakeTape)
        self.assertEqual(len(details), 1)
        self.assertEqual(len(adapted), len(rows))
        self.assertTrue(_shape(adapted, FakeKeywords.TOKEN, True))
        changed = [n for (n, old), (_, new) in zip(rows, adapted) if old != new]
        self.assertEqual(changed, [632, 3000, 3270, 5008, 9000, 9020])
        self.assertIn(b'USR "a"-1024', dict(adapted)[9020])
        self.assertNotIn(b'23606', dict(adapted)[632])

    def test_genuine_rom_slice(self):
        rom = bytes(range(256))*64
        self.assertEqual(rom_font(rom), rom[15616:16384])
        self.assertEqual(len(rom_font(rom)), 768)
        with self.assertRaises(ValueError):
            rom_font(b'incomplete')

    def test_only_three_bounded_accesses_approved(self):
        rows, detail = adapt_scuba_charset(archive_rows(), FakeKeywords, None,
                                           FakeSource, FakeTape)
        self.assertTrue(detail)
        findings = [
            SimpleNamespace(line=5008, operation='POKE', severity='block',
                            classification='unbounded_memory_write',
                            expression='USR "a"-1024+(K+33)*8+J,A'),
            SimpleNamespace(line=9000, operation='PEEK', severity='block',
                            classification='unbounded_memory_read',
                            expression='(USR "a"-768)=255 THEN GO TO 9060'),
            SimpleNamespace(line=9020, operation='POKE', severity='block',
                            classification='unbounded_memory_write',
                            expression='USR "a"-1024+X,'),
        ]
        self.assertEqual(allow_scuba_font_access(rows, FakeKeywords.TOKEN, findings), 3)
        self.assertTrue(all(f.severity == 'info' for f in findings))
        malicious = archive_rows()
        self.assertEqual(allow_scuba_font_access(malicious, FakeKeywords.TOKEN, findings), 0)
        rows2, _ = adapt_scuba_charset(archive_rows(), FakeKeywords, None,
                                       FakeSource, FakeTape)
        other = [SimpleNamespace(line=700, operation='POKE', severity='block',
                                 expression='60000,0', classification='global_memory_write')]
        self.assertEqual(allow_scuba_font_access(rows2, FakeKeywords.TOKEN, other), 0)


if __name__ == '__main__':
    unittest.main()
