"""Execute native CHARS virtualization; no write to ZX-UX's global CHARS."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_sysvars_rt import _native_peek, _native_poke, BSS_BYTES
from z80asm import asm
from z80mini import Z80


class NativeChars(unittest.TestCase):
    def setUp(self):
        self.memory = bytearray(65536)
        self.virtual_base = 0x8000
        self.peek_entry = 0x7000
        self.poke_entry = 0x7200
        peek = _native_peek(asm, 0x1000, 0x7000, 0x1400)
        poke = _native_poke(asm, 0x1000, 0x7000, 0x1400, entry=0x200)
        self.memory[self.peek_entry:self.peek_entry+len(peek)] = peek
        self.memory[self.poke_entry:self.poke_entry+len(poke)] = poke
        self.cpu = Z80(self.memory)
        self.cpu.sp = 0x9000
        self.memory[0x5c36] = 0x00
        self.memory[0x5c37] = 0x80

    def peek(self, addr):
        self.cpu.hl = addr
        self.cpu.call(self.peek_entry)
        return self.cpu.hl

    def poke(self, addr, value):
        self.cpu.hl = addr
        self.cpu.e = value
        self.cpu.call(self.poke_entry)

    def test_initial_48k_chars_pointer(self):
        self.assertEqual(self.peek(23606), 0)
        self.assertEqual(self.peek(23607), 0x3c)

    def test_low_high_writes_are_process_private(self):
        self.poke(23606, 0x60)
        self.poke(23607, 0xeb)
        self.assertEqual([self.peek(23606), self.peek(23607)], [0x60,0xeb])
        self.assertEqual([self.memory[0x5c36], self.memory[0x5c37]], [0x00,0x80])

    def test_low_write_does_not_wipe_default_high(self):
        self.poke(23606, 0x80)
        self.assertEqual(self.peek(23606), 0x80)
        self.assertEqual(self.peek(23607), 0x3c)

    def test_font_bytes_map_to_process_owned_glyphs(self):
        # The real CHARS system variable is set to a private font by the
        # native SSX entry, while the BASIC program sees its historical RAM
        # character bank at 0xEB60 (Scuba-style pointer).
        self.memory[0x5c36] = 0x00
        self.memory[0x5c37] = 0x80
        self.poke(23606, 0x60)
        self.poke(23607, 0xeb)
        self.poke(0xec60, 0x91)
        self.assertEqual(self.memory[0x8100], 0x91)
        self.assertEqual(self.memory[0xec60], 0)
        self.assertEqual(self.peek(0xec60), 0x91)
        self.assertEqual(self.memory[0x5c36:0x5c38], b'\x00\x80')

    def test_rom_and_private_font_switches_are_actual_and_safe(self):
        self.poke(23606,0)
        self.poke(23607,60)
        self.assertEqual(self.memory[0x5c36:0x5c38],b'\x00\x3c')
        self.poke(23606,0x60)
        self.poke(23607,0xeb)
        self.assertEqual(self.memory[0x5c36:0x5c38],b'\x00\x80')
        self.poke(0xec60,0x7c)
        self.assertEqual(self.memory[0x8100],0x7c)
        self.poke(23606,0)
        self.poke(23607,60)
        self.assertEqual(self.memory[0x5c36:0x5c38],b'\x00\x3c')
        self.poke(23606,0x60)
        self.poke(23607,0xeb)
        self.assertEqual(self.peek(0xec60),0x7c)

    def test_font_alias_rejects_outside_printable_range(self):
        self.memory[0x5c36:0x5c38] = b'\x00\x80'
        self.poke(23606, 0x60)
        self.poke(23607, 0xeb)
        self.cpu.hooks[8] = lambda cpu: (_ for _ in ()).throw(PermissionError('not private glyph'))
        for addr in (0xeb5f, 0xef60, 0xf160):
            with self.subTest(addr=addr):
                with self.assertRaises(PermissionError):
                    self.poke(addr, 0x56)

    def test_statically_selected_bank_works_before_chars_poke(self):
        # Source analysis selects the bank as an allocation hint only.
        # Actual virtual CHARS still starts at its genuine 48K value.
        bank=0xeb60
        peek=_native_peek(asm,0x1000,0x7000,0x1400,font_alias=bank)
        poke=_native_poke(asm,0x1000,0x7000,0x1400,font_alias=bank,entry=0x200)
        self.memory[self.peek_entry:self.peek_entry+len(peek)]=peek
        self.memory[self.poke_entry:self.poke_entry+len(poke)]=poke
        self.memory[0x5c36:0x5c38]=b'\x00\x80'
        self.assertEqual(self.peek(23607),0x3c)
        self.poke(bank,0x77)
        self.poke(bank+1023,0xa9)
        self.assertEqual(self.memory[0x8000],0x77)
        self.assertEqual(self.memory[0x83ff],0xa9)
        self.assertEqual(self.peek(bank),0x77)
        self.assertEqual(self.peek(23607),0x3c)

    def test_cannot_redirect_virtual_font_into_kernel(self):
        self.poke(23606,0x60)
        self.poke(23607,0xeb)
        self.memory[self.virtual_base+11:self.virtual_base+14]=b'\x00\xa0\x01'
        def unsafe(cpu):
            raise PermissionError('out of process font destination')
        self.cpu.hooks[8]=unsafe
        with self.assertRaises(PermissionError):
            self.poke(0xeb60,0x72)
        self.assertEqual(self.memory[0xa000],0)

    def test_process_bss_is_respected(self):
        self.assertGreaterEqual(BSS_BYTES, 11)
        self.assertEqual(self.memory[self.virtual_base+11:self.virtual_base+20], bytes(9))


if __name__ == '__main__':
    unittest.main()
