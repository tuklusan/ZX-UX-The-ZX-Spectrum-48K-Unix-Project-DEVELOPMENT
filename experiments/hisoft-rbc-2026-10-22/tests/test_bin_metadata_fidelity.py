"""Regression: literal {C4} BIN metadata is binary, not decimal.

Exercises the strict text adapter without modifying the frozen BAS2TAP port,
original source files, or already published SSX binaries.
"""
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'stage'))
from bas2tap import encode_program, tokenize_line
from basic_listing import _fix_bin_cache, encode_strict_listing
from dual_source import validated_lines, semantic_check


class BinaryTokenCache(unittest.TestCase):
    def test_frozen_upstream_remains_unchanged(self):
        frozen = ROOT / 'stage' / 'bas2tap.py'
        self.assertEqual(hashlib.sha256(frozen.read_bytes()).hexdigest(),
                         'c12d852652366162cb4787ebfc149fd91bc36d09fcbf8c1e44dc75b572fd016d')

    def test_escape_matches_real_bin_token(self):
        bits = ('0', '1', '00000011', '00000111', '00001111',
                '10101010', '11111111', '1111111111111111')
        for literal in bits:
            with self.subTest(bits=literal):
                direct = encode_strict_listing('10 DATA BIN ' + literal)
                escaped = encode_strict_listing('10 DATA {C4}' + literal)
                self.assertEqual(escaped, direct)
                self.assertEqual(escaped[-7:-2], b'\x0e\x00\x00' +
                                 int(literal, 2).to_bytes(2, 'little'))

    def test_raw_frozen_port_exhibits_bug_and_adapter_fixes_it(self):
        listing = '10 DATA {C4}10101010'
        raw = encode_program(listing)
        corrected = encode_strict_listing(listing)
        self.assertNotEqual(raw, corrected)
        self.assertEqual(raw[-7:-1], b'\x0e' + encode_program('10 DATA 10101010')[-6:-1])
        self.assertEqual(corrected[-7:-1], b'\x0e\x00\x00\xaa\x00\x00')

    def test_inert_text_is_preserved(self):
        for text in ('10 PRINT "{C4}10101010"',
                     '10 REM {C4}10101010',
                     '10 DATA "{C4}10101010"',
                     '10 PRINT "BIN 10101010": REM {C4}1001'):
            with self.subTest(text=text):
                self.assertEqual(encode_strict_listing(text), encode_program(text))

    def test_existing_explicit_bin_is_unchanged(self):
        for text in ('10 LET A=BIN 10101010',
                     '10 PRINT BIN 00000111',
                     '10 DATA BIN 10101010,255,5'):
            with self.subTest(text=text):
                self.assertEqual(encode_strict_listing(text), encode_program(text))

    def test_bad_or_incomplete_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exceeds 65535'):
            _fix_bin_cache(b'\xe4\xc4' + b'1'*17 + b'\x0e\x00\x00\x00\x00\x00\x0d', 10)
        with self.assertRaisesRegex(ValueError, 'incomplete numeric cache'):
            _fix_bin_cache(b'\xe4\x31\x0e\x00\x0d', 10)

    def test_original_mushroom_binary_data(self):
        path = ROOT.parents[1] / 'src/bonus/60-programs/59-mushroom-invasion/BASIC/59-mushroom-invasion.bas'
        if not path.is_file():
            self.skipTest('authoritative BAS not mounted')
        lines = dict(validated_lines(encode_strict_listing(path.read_text(encoding='ascii'))))
        line = lines[1020]
        values = []
        pos = 0
        while pos < len(line):
            if line[pos] == 0xC4:
                end = line.index(14, pos)
                values.append(int.from_bytes(line[end + 3:end + 5], 'little'))
                pos = end + 6
            else:
                pos += 1
        self.assertEqual(values, [3, 7, 15, 170, 170, 15, 7, 3])

    def test_mushroom_tape_matches_authoritative_binary_bytes(self):
        path = ROOT.parents[1] / 'src/bonus/60-programs/59-mushroom-invasion/BASIC/59-mushroom-invasion.bas'
        if not path.is_file():
            self.skipTest('authoritative BAS/TZX not mounted')
        tape = path.with_suffix('.tzx').read_bytes()
        self.assertTrue(tape.startswith(b'ZXTape!\x1a'))
        blocks = []
        index = 10
        while index < len(tape):
            self.assertEqual(tape[index], 0x10)
            size = int.from_bytes(tape[index + 3:index + 5], 'little')
            index += 5
            block = tape[index:index + size]
            index += size
            self.assertEqual(len(block), size)
            self.assertEqual(0, 0 if not block else __import__('functools').reduce(
                lambda a, b: a ^ b, block, 0))
            blocks.append(block)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][:2], b'\x00\x00')
        self.assertEqual(blocks[1][0], 0xFF)
        expected_bytes = int.from_bytes(blocks[0][12:14], 'little')
        program = blocks[1][1:-1]
        self.assertEqual(len(program), expected_bytes)
        bas_bytes = encode_strict_listing(path.read_text(encoding='ascii'))
        self.assertEqual(dict(validated_lines(bas_bytes))[1020],
                         dict(validated_lines(program))[1020])
        from bas2tap import TOKENS
        semantic_check(bas_bytes, program, validated_lines, TOKENS, 'mushroom')


if __name__ == '__main__':
    unittest.main()
