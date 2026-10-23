"""Preserve the original Paypackets numeric AT name in its BASIC listing."""
import re
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from basic_listing import tokenize_preserving_numeric_at


class Keywords:
    CODE_FOR = {'AT': 0xac}


class Tokenizer:
    @staticmethod
    def tokenize_line(line, kw):
        return re.sub(rb'\bAT\b', bytes((kw.CODE_FOR['AT'],)), line.encode())


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        src = cls.root / 'src' / 'bonus' / '60-programs' / '17-paypackets' / 'BASIC'
        cls.basic = src / '17-paypackets.bas'
        cls.tzx = src / '17-paypackets.tzx'

    def listing(self):
        numbered = {}
        for line in self.basic.read_text().splitlines():
            found = re.fullmatch(r'(\d+)\s+(.*)', line)
            if found:
                numbered[int(found[1])] = found[2]
        return numbered

    def test_preserved_original_statements(self):
        if not self.basic.exists():
            self.skipTest('Original BASIC collection is absent')
        numbered = self.listing()
        for number in (500, 539, 574, 575):
            with self.subTest(number=number):
                output = tokenize_preserving_numeric_at(numbered[number], Tokenizer(), Keywords())
                self.assertNotIn(bytes((0xac,)), output)
                self.assertIn(b'AT', output)

    def test_print_position_keyword_unchanged(self):
        value = tokenize_preserving_numeric_at('PRINT AT 2,0;"HELLO"', Tokenizer(), Keywords())
        self.assertIn(bytes((0xac,)), value)

    def test_other_numeric_identifier_unchanged(self):
        value = tokenize_preserving_numeric_at('LET MAT=5', Tokenizer(), Keywords())
        self.assertEqual(value, b'LET MAT=5')

    def test_strict_source_shape(self):
        value = tokenize_preserving_numeric_at('LET AT=123', Tokenizer(), Keywords())
        self.assertIn(bytes((0xac,)), value)

    def test_original_tape_token_parity(self):
        upstream = self.root / 'upstream-pyhsb'
        if not (upstream / 'source.py').exists():
            self.skipTest('Upstream tokenizer checkout is absent')
        sys.path.insert(0, str(upstream))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'zxux_original_source', upstream / 'source.py')
        source = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(source)
        rom = (self.root / 'src/zx-ux-sdk/rom/48.rom').read_bytes()
        kw = source.Keywords(rom)
        tape = self.tzx.read_bytes()
        self.assertTrue(tape.startswith(b'ZXTape!\x1a'))
        blocks = []
        pos = 10
        while pos < len(tape):
            self.assertEqual(tape[pos], 16)
            size = int.from_bytes(tape[pos + 3:pos + 5], 'little')
            blocks.append(tape[pos + 5:pos + 5 + size])
            pos += 5 + size
        program = blocks[1][1:-1]
        rows = {}
        pos = 0
        while pos < len(program):
            number = int.from_bytes(program[pos:pos + 2], 'big')
            size = int.from_bytes(program[pos + 2:pos + 4], 'little')
            rows[number] = program[pos + 4:pos + 4 + size]
            pos += 4 + size
        self.assertEqual(pos, len(program))
        for number in (500, 539, 574, 575):
            with self.subTest(number=number):
                actual = tokenize_preserving_numeric_at(self.listing()[number], source, kw) + b'\r'
                raw = rows[number]
                without_hidden = bytearray()
                i = 0
                while i < len(raw):
                    if raw[i] == 14:
                        i += 6
                    else:
                        without_hidden.append(raw[i])
                        i += 1
                self.assertEqual(actual, bytes(without_hidden))


if __name__ == '__main__':
    unittest.main()
