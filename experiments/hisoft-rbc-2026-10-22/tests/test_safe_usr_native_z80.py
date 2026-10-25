"""Execute the process UDG address guard on the bundled Z80 CPU."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
sys.path.insert(0, str(ROOT / 'upstream-pyhsb'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from safe_usr_rt import UDG_POKE_CHECK
from z80_python.cpu import Z80CPU

EXPECTED = bytes.fromhex('e5ed5b7b5cb7ed52380c7cb720087dfea83003e1180f2a7b5c01a800097e23666f110b00e9c9')


def execute(data, displacement):
    image = bytearray(65536)
    # Native errors call the process-exit service, never the ROM panic handler.
    image[0x9000:0x9000 + len(data)] = data
    image[0x5c7b:0x5c7d] = (0xa000).to_bytes(2, 'little')
    image[0xfe00:0xfe02] = (0xa1bc).to_bytes(2, 'little')
    image[0xa000:0xa0a8] = bytes([0x5a]) * 168
    image[0xa0a8:0xa0aa] = (0x7200).to_bytes(2, 'little')
    cpu = Z80CPU(image.__getitem__, image.__setitem__)
    cpu.pc = 0x9000
    cpu.sp = 0xfe00
    candidate = (0xa000 + displacement) & 0xffff
    cpu.h, cpu.l = candidate >> 8, candidate & 255
    destination = None
    for _ in range(64):
        if cpu.pc == 0x0008 or cpu.pc == 0x6003:
            raise AssertionError('UDG guard entered kernel or ROM error handler')
        if cpu.pc == 0xa1bc:
            destination = 'accepted'
            break
        if cpu.pc == 0x7200:
            if (cpu.d << 8 | cpu.e) != 11:
                raise AssertionError('native trampoline lost error status')
            destination = 'blocked'
            break
        cpu.step()
    return destination, (cpu.h << 8) | cpu.l, bytes(image[0xa000:0xa0a8])


class UdgNativeCheck(unittest.TestCase):
    def test_emission_is_the_exact_z80_guard(self):
        from z80asm import asm
        self.assertEqual(asm(UDG_POKE_CHECK) + b"\xc9", EXPECTED)

    def test_guard_allows_only_owned_udg_bytes(self):
        for offset in (-100, -1, 0, 1, 7, 8, 159, 167, 168, 169, 256, 320, 512, 2000):
            with self.subTest(offset=offset):
                outcome, hl, image = execute(EXPECTED, offset)
                accepted = 0 <= offset < 168
                self.assertEqual(outcome, 'accepted' if accepted else 'blocked')
                self.assertEqual(image, bytes([0x5a]) * 168)
                if accepted:
                    self.assertEqual(hl, 0xa000 + offset)


if __name__ == '__main__':
    unittest.main()
