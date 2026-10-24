"""Execute native Z80 system-variable routines against a memory-isolated CPU."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from spectrum_sysvars import FLAGS2, PIP, FRAMES
from native_sysvars_rt import _native_peek, _native_poke, BSS_BYTES
from z80asm import asm
from z80mini import Z80

class NativeSysvars(unittest.TestCase):
    def setUp(self):
        self.mem = bytearray(65536)
        self.base = 0x8000
        self.peek_addr = 0x7000
        self.poke_addr = 0x7200
        # The Z80 helpers contain absolute branches; place them at their
        # actual test addresses and share the process BSS base.
        offset = self.base - self.peek_addr
        self.mem[self.peek_addr:self.peek_addr+256] = _native_peek(asm,offset,self.peek_addr)
        self.mem[self.poke_addr:self.poke_addr+256] = _native_poke(asm,offset,self.peek_addr,entry=self.poke_addr-self.peek_addr)
        self.cpu = Z80(self.mem)
        self.cpu.sp = 0x9000
        self.ticks = 0
        def syscall(cpu):
            self.assertEqual(cpu.a,38)
            cpu.hl = self.ticks
        self.cpu.hooks[0x6003] = syscall
        self.rom_before = {addr: 0xcc for addr in (PIP,FLAGS2,*FRAMES)}
        for addr,byte in self.rom_before.items(): self.mem[addr] = byte

    def poke(self,addr,value):
        self.cpu.hl = addr; self.cpu.e = value & 255
        self.cpu.call(self.poke_addr)

    def peek(self,addr):
        self.cpu.hl = addr
        self.cpu.call(self.peek_addr)
        return self.cpu.hl

    def test_system_values_are_private_and_byte_exact(self):
        self.poke(FLAGS2,0x55)
        self.poke(PIP,0x23)
        self.assertEqual(self.peek(FLAGS2),0x55)
        self.assertEqual(self.peek(PIP),0x23)
        self.assertEqual({a:self.mem[a] for a in self.rom_before},self.rom_before)

    def test_three_frame_bytes_are_private_and_roll_over(self):
        for addr in FRAMES:self.poke(addr,0xff)
        self.assertEqual([self.peek(addr) for addr in FRAMES],[255]*3)
        self.ticks=1
        self.assertEqual([self.peek(addr) for addr in FRAMES],[0,0,0])
        self.assertEqual({a:self.mem[a] for a in self.rom_before},self.rom_before)

    def test_clock_carries_across_16_bit_rollover(self):
        self.ticks=65534
        self.assertEqual(self.peek(FRAMES[0]),0)
        self.poke(FRAMES[0],254)
        self.ticks=1
        self.assertEqual([self.peek(addr) for addr in FRAMES],[1,1,0])

    def test_other_memory_peek_poke_remains_functional(self):
        self.poke(0x5801, 0x2f)
        self.assertEqual(self.peek(0x5801),0x2f)
        self.assertEqual(self.mem[0x5801],0x2f)

    def test_rejects_protected_kernel_peek_and_poke(self):
        def unsafe(cpu):
            raise PermissionError('protected memory rejected by native runtime')
        self.cpu.hooks[8] = unsafe
        for address in (0x5b00, 0x5c00, 0x6003, 0xa000):
            with self.subTest(address=address, operation='PEEK'):
                with self.assertRaises(PermissionError):
                    self.peek(address)
            with self.subTest(address=address, operation='POKE'):
                with self.assertRaises(PermissionError):
                    self.poke(address, 0x65)
        self.assertEqual({a:self.mem[a] for a in self.rom_before},self.rom_before)

    def test_allow_private_process_data_but_not_other_memory(self):
        # The native linker relocates original offsets from a code base.
        # Simulate code at 0x7000 and a process BSS offset of 0x1000.
        self.mem[self.peek_addr:self.peek_addr+256] = _native_peek(asm,0x1000,0x7000,0x1008)
        self.mem[self.poke_addr:self.poke_addr+256] = _native_poke(asm,0x1000,0x7000,0x1008,entry=self.poke_addr-self.peek_addr)
        self.cpu.hooks[8] = lambda cpu: (_ for _ in ()).throw(PermissionError('out of process'))
        self.mem[self.base] = 0x66
        self.assertEqual(self.peek(self.base), 0x66)
        self.poke(self.base, 0x54)
        self.assertEqual(self.peek(self.base), 0x54)
        with self.assertRaises(PermissionError):
            self.peek(self.base + BSS_BYTES + 10)

    def test_original_rom_keyboard_scan_service_survives(self):
        def scan(cpu):
            self.mem[23556] = 42
        self.cpu.hooks[0x02bf] = scan
        self.assertEqual(self.peek(23556),42)
        self.assertEqual(self.mem[23556],42)

    def test_rom_writes_are_blocked_but_rom_reads_work(self):
        def unsafe(cpu):
            raise PermissionError('write to ROM rejected')
        self.cpu.hooks[8] = unsafe
        self.mem[0x1234] = 0x55
        self.assertEqual(self.peek(0x1234), 0x55)
        with self.assertRaises(PermissionError):
            self.poke(0x1234, 0xaa)
        self.assertEqual(self.mem[0x1234], 0x55)

    def test_no_compiler_bss_outside_allocation(self):
        self.poke(FLAGS2,0x55)
        self.poke(PIP,0x33)
        self.peek(FRAMES[0])
        self.assertEqual(self.mem[self.base+BSS_BYTES:self.base+BSS_BYTES+8], bytes(8))

if __name__ == '__main__':unittest.main()
