"""ROM LIST-format and original TZX extraction regressions.

Run using a checked-out DEVELOPMENT repository (and its frozen 48K ROM),
or set ZX_ROM and MINELAY_TZX to local matching bytes.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / 'stage' / 'tzx-basic-lister.py'
SPEC = importlib.util.spec_from_file_location('tzx_basic_lister', TOOL)
LISTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LISTER)
ROM_PATH = Path(os.environ.get('ZX_ROM', str(HERE.parents[2] / 'src/zx-ux-sdk/rom/48.rom')))
TZX_PATH = Path(os.environ.get('MINELAY_TZX', str(HERE.parents[2] / 'src/bonus/60-programs/01-minelay/BASIC/01-minelay.tzx')))


def block(flag: int, payload: bytes) -> bytes:
    raw = bytes([flag]) + payload
    xor = 0
    for c in raw:
        xor ^= c
    return raw + bytes([xor])


def tape_from_program(program: bytes, name=b'MINI') -> bytes:
    header = (bytes([0]) + name.ljust(10, b' ') + len(program).to_bytes(2, 'little')
              + bytes.fromhex('0080') + len(program).to_bytes(2, 'little'))
    parts = []
    for payload in (block(0, header), block(255, program)):
        parts.append(b'\x10\xe8\x03' + len(payload).to_bytes(2, 'little') + payload)
    return b'ZXTape!\x1a\x01\x14' + b''.join(parts)


def line(number: int, body: bytes) -> bytes:
    full = body + b'\r'
    return number.to_bytes(2, 'big') + len(full).to_bytes(2, 'little') + full


@unittest.skipUnless(ROM_PATH.is_file(), 'requires original 48K ROM')
class ListSpacing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.tokens = LISTER.rom_keywords(cls.rom)

    def test_48k_rom_table(self):
        self.assertEqual(len(self.tokens), 91)
        self.assertEqual(self.tokens[0xa5], b'RND')
        self.assertEqual(self.tokens[0xcb], b'THEN')
        self.assertEqual(self.tokens[0xff], b'COPY')

    def test_exact_line_number_and_keyword_spacing(self):
        self.assertEqual(LISTER.list_line(20, b'\xe1', self.rom), '  20 LLIST ')
        self.assertEqual(LISTER.list_line(20, b'\xe0', self.rom), '  20 LPRINT ')
        self.assertEqual(LISTER.list_line(20, b'\xe4', self.rom), '  20 DATA ')
        self.assertEqual(LISTER.list_line(20, b'\xf4', self.rom), '  20 POKE ')
        self.assertEqual(LISTER.list_line(20, b'\xf5', self.rom), '  20 PRINT ')
        self.assertEqual(LISTER.list_line(20, b'\xe2', self.rom), '  20 STOP ')
        self.assertEqual(LISTER.list_line(5, b'\xf5\xc2(147)', self.rom),
                         '   5 PRINT CHR$ (147)')

    def test_minelay_keyword_boundary(self):
        self.assertEqual(LISTER.list_line(700, b'\xfa\xa5>sk\xcb\xf5', self.rom),
                         ' 700 IF RND>sk THEN PRINT ')
        self.assertEqual(LISTER.list_line(122, b'\xfaa=7\xcb\xfa', self.rom),
                         ' 122 IF a=7 THEN IF ')

    def test_spaces_from_rom_flags(self):
        # An explicit space suppresses an additional leading space.
        self.assertEqual(LISTER.list_line(10, b'\xfaa=1 \xcb\xf5', self.rom),
                         '  10 IF a=1 THEN PRINT ')
        # These three tokens have no default trailing space in ROM.
        self.assertEqual(LISTER.list_line(10, b'\xf5\xa5>0', self.rom),
                         '  10 PRINT RND>0')
        self.assertEqual(LISTER.list_line(10, b'\xf5\xa6', self.rom),
                         '  10 PRINT INKEY$')

    def test_binary_data_uses_safe_ascii_escapes(self):
        self.assertEqual(LISTER.list_line(12, b'\xf5"\x92{40}"', self.rom),
                         '  12 PRINT "{92}{7B}40{7D}"')
        self.assertEqual(LISTER.list_line(13, b'\xea \xf5"', self.rom),
                         '  13 REM  {F5}"')

    def test_original_numeric_cache_skipped(self):
        data = b'\xfaa=7\x0e\x00\x00\x07\x00\x00\xcb\xf5'
        self.assertEqual(LISTER.list_line(122, data, self.rom),
                         ' 122 IF a=7 THEN PRINT ')
        with self.assertRaisesRegex(LISTER.TapeError, 'truncated'):
            LISTER.list_line(122, b'\xf5 1\x0e\x00', self.rom)

    def test_data_numeric_cache_and_literal_quote(self):
        self.assertEqual(LISTER.list_line(100, b'\xe4 34\x0e\x00\x00\x22\x00\x00',
                                          self.rom), ' 100 DATA  34')

    def test_round_trip_tape_extract(self):
        original = line(122, b'\xfaa=7\xcb\xf5"OK"')
        tape = tape_from_program(original)
        self.assertEqual(list(LISTER.basic_programs(tape))[0][1], original)
        self.assertEqual(LISTER.listing(tape, self.rom), ' 122 IF a=7 THEN PRINT "OK"\n')

    def test_bad_checksum_rejected(self):
        image = bytearray(tape_from_program(line(10, b'\xf5"OK"')))
        image[-1] ^= 1
        with self.assertRaisesRegex(LISTER.TapeError, 'checksum'):
            list(LISTER.basic_programs(bytes(image)))

    def test_multiple_programs_rejected_unless_selected(self):
        tape = tape_from_program(line(10, b'\xf5"A"'))
        tape += tape_from_program(line(20, b'\xf5"B"'))[10:]
        with self.assertRaisesRegex(LISTER.TapeError, '2 BASIC programs'):
            LISTER.listing(tape, self.rom)
        self.assertIn('B', LISTER.listing(tape, self.rom, program_index=1))

    def test_protected_original_destination(self):
        path = Path('/tmp/z/src/bonus/60-programs/01-minelay/BASIC/01-minelay.bas')
        self.assertTrue(LISTER._protected_listing_destination(path))
        self.assertFalse(LISTER._protected_listing_destination(
            Path('/tmp/z/build/tmp/listings/01-minelay/BASIC/01-minelay.bas')))


    def test_corpus_if_present(self):
        base = HERE.parents[2] / 'src/bonus/60-programs'
        if not base.is_dir():
            self.skipTest('original 60-program corpus not mounted')
        games = sorted(p for p in base.iterdir() if p.is_dir() and p.name[:2].isdigit()
                       and p.name[2:3] == '-')
        self.assertEqual(len(games), 60)
        for game in games:
            tape = game / 'BASIC' / (game.name + '.tzx')
            with self.subTest(game=game.name):
                text = LISTER.listing(tape.read_bytes(), self.rom)
                self.assertTrue(text.endswith('\n'))
                self.assertGreater(len(text.splitlines()), 0)

    def test_no_overwrite_and_staged_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / 'test.tzx'
            output_path = Path(tmp) / 'staged.bas'
            input_path.write_bytes(tape_from_program(line(20, b'\xe2')))
            args = [str(input_path), '--rom', str(ROM_PATH), '-o', str(output_path)]
            first = subprocess.run([sys.executable, str(TOOL), *args],
                                   capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = output_path.read_bytes()
            second = subprocess.run([sys.executable, str(TOOL), *args],
                                    capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output_path.read_bytes(), original)

    @unittest.skipUnless(TZX_PATH.is_file(), 'requires preserved Minelay tape')
    def test_real_minelay(self):
        converted = LISTER.listing(TZX_PATH.read_bytes(), self.rom)
        self.assertEqual(len(converted.splitlines()), 81)
        self.assertIn(' 122 IF a=7 THEN IF a$="{92}" THEN GO TO 5000', converted)
        self.assertIn('sk THEN PRINT', converted)
        # Actual output requires no C compiler or dependencies.
        result = subprocess.run([sys.executable, str(TOOL), str(TZX_PATH),
                                 '--rom', str(ROM_PATH)], check=True,
                                capture_output=True, text=True)
        self.assertEqual(result.stdout, converted)


if __name__ == '__main__':
    unittest.main()

@unittest.skipUnless(ROM_PATH.is_file(), 'requires original 48K ROM')
class OriginalZ80LLISTConformance(unittest.TestCase):
    """Run real 48K Z80 instructions at LLIST's common OUT-LINE entry.

    Capture RST 10 characters before the bitmap printer implementation, using
    a channel shim. Search, token spelling, character iteration, line-number
    printing, numeric cache skipping and spacing execute original ROM bytes,
    independently of the Python LLIST translation being tested.
    """
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        sdk = Path(os.environ.get('ZX_SDK', str(HERE.parents[2] / 'src/zx-ux-sdk')))
        sys.path.insert(0, str(sdk))
        from z80_python.cpu import Z80CPU
        cls.CPU = Z80CPU

    def rom_output(self, number, body):
        memory = bytearray(0x10000)
        memory[:0x4000] = self.rom
        raw = line(number, body)
        memory[0x8000:0x8000 + len(raw)] = raw
        # Set E-PPC, K-CUR and X-PTR so the test is an ordinary LLIST line,
        # not the editor's special current-line/cursor/error rendering mode.
        memory[0x5C49:0x5C4B] = (9998).to_bytes(2, 'little')
        memory[0x5C5B:0x5C5D] = (0xFFFF).to_bytes(2, 'little')
        memory[0x5C5F:0x5C61] = (0xFFFF).to_bytes(2, 'little')
        cpu = self.CPU(memory.__getitem__, memory.__setitem__)
        cpu.pc, cpu.h, cpu.l, cpu.iy, cpu.sp = 0x1855, 0x80, 0, 0x5C3A, 0xF000
        memory[0xF000:0xF002] = (0xA000).to_bytes(2, 'little')
        result = bytearray()
        pending = []
        for _ in range(300000):
            if cpu.pc == 0xA000:
                return bytes(result)
            if cpu.pc == 0xA001:
                ret, registers = pending.pop()
                cpu.d, cpu.e, cpu.h, cpu.l, cpu.b, cpu.c = registers
                cpu.pc = ret
                continue
            if cpu.pc == 0x15EF:  # OUT-CODE's channel: print digit
                cpu.e = 0x30
                value = (cpu.a + 0x30) & 255
                result.append(value)
                if 32 <= value < 128:
                    memory[0x5C3B] = (memory[0x5C3B] & ~1) | int(value == 32)
                cpu.pc = cpu._pop_word()
                continue
            if cpu.pc == 0x0010:  # ROM RST 10: intercept physical printer only
                value = cpu.a
                if value >= 0xA5:
                    # 0C10/0C41/0C22/0C35 run as real Z80 ROM code.
                    ret = cpu._pop_word()
                    pending.append((ret, (cpu.d, cpu.e, cpu.h, cpu.l, cpu.b, cpu.c)))
                    cpu._push_word(0xA001)
                    cpu.a = value - 0xA5
                    cpu.pc = 0x0C10
                else:
                    result.append(value)
                    if 32 <= value < 128:
                        memory[0x5C3B] = (memory[0x5C3B] & ~1) | int(value == 32)
                    cpu.pc = cpu._pop_word()
                continue
            cpu.step()
        self.fail(f'original ROM OUT-LINE never returned: PC=0x{cpu.pc:04X}')

    def verify(self, number, body):
        actual = self.rom_output(number, body)
        calculated = LISTER.llist_codes(number, body, self.rom)
        self.assertEqual(calculated, actual,
                         f'line {number}, BASIC bytes {body.hex()}')

    def test_all_91_original_rom_keywords(self):
        for token in range(0xA5, 0x100):
            with self.subTest(token=hex(token)):
                self.verify(10, bytes([token]))
                self.verify(700, b'\xfa a=1' + bytes([token]) + b'b')

    def test_actual_minelay_every_line(self):
        if not TZX_PATH.is_file():
            self.skipTest('Minelay original TZX not mounted')
        programs = list(LISTER.basic_programs(TZX_PATH.read_bytes()))
        self.assertEqual(len(programs), 1)
        rows = list(LISTER.numbered_lines(programs[0][1]))
        self.assertEqual(len(rows), 81)
        for number, body in rows:
            with self.subTest(number=number):
                self.verify(number, body)

    def test_raw_tokens_in_quotes_are_still_expanded_by_rom(self):
        body = b'\xf5"\xf5"'
        rom = self.rom_output(100, body)
        self.assertEqual(rom, b' 100 PRINT " PRINT "')
        self.assertEqual(LISTER.list_line(100, body, self.rom),
                         ' 100 PRINT "{F5}"')

    def test_number_caches_and_spacings(self):
        for number, body in (
            (0, b'\xf5 1'), (9999, b'\xf5 2'),
            (100, b'\xe4 34\x0e\x00\x00\x22\x00\x00'),
            (500, b'\xfa x=1\x0e\x00\x00\x01\x00\x00\xcb\xf5'),
            (10, b'\xf5\xa5>0'), (10, b'\xf5\xa6'),
            (10, b'\xf5\x90\xcb'), (10, b'\xf5\x80\xcb'),
            (10, b'\xf5\x16\x02\x03\xcb'), (10, b'\xf5\x60\xcb'),
            (10, b'\xf5\xea\x20\x01\x02'),
        ):
            with self.subTest(number=number, body=body.hex()):
                self.verify(number, body)
