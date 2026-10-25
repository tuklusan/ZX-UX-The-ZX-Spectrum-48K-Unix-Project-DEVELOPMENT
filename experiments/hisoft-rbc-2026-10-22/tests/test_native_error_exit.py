"""Execute shared native failure cleanup in an SSX-linked Z80 image."""
from pathlib import Path
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / 'experiments/hisoft-rbc-2026-10-22/stage'
sys.path.insert(0, str(STAGE))
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
from native_error_exit import UDG_BYTES, error_exit_bytes, error_exit_asm
from z80_python.cpu import Z80CPU
import rld


class NativeErrorExit(unittest.TestCase):
    def test_native_dispatch_encoding(self):
        for status in (0, 10, 11, 255):
            self.assertEqual(len(error_exit_bytes(status)), 15)
            self.assertIn(f'ld de,{status}', error_exit_asm(status))
        for status in (-1, 256):
            with self.assertRaises(ValueError):
                error_exit_bytes(status)

    def test_linked_wrapper_restores_every_exit(self):
        path = Path(os.getenv('RBC_GATE7_CHECKPOINT', str(
            ROOT / 'build/tmp/rbc-round2/current/rbc')))
        if not (path / 'rbc.py').is_file():
            self.skipTest('Requires a prepared HiSoft RBC checkpoint')
        sys.path.insert(0, str(path))
        import rbc
        font = bytes((i * 13) & 255 for i in range(768))
        original = {0x5c36:0x00,0x5c37:0x3c,0x5c7b:0x00,0x5c7c:0xfc,
                    0x5c6a:0xbb,0x5c39:0x34,0x5c8d:0x48,
                    0x5c8e:0x72,0x5c8f:0x4d,0x5c90:0x16}
        for rom_font in (False, True):
            for status in (None, 10, 11):
                with self.subTest(rom_font=rom_font,status=status):
                    # Change process UDG, actual CHARS and shell control
                    # bytes before returning or jumping to the shared exit.
                    code = (bytes.fromhex('2a7b5c3649'  # LD HL,(UDG); LD (HL),73
                                          '21444422365c'  # CHARS=0x4444
                                          '3e88326a5c'    # FLAGS2=0x88
                                          '3e9932395c'    # PIP=0x99
                                          '3e22328d5c')   # Color=0x22
                            + (b'\xc9' if status is None else error_exit_bytes(status)))
                    builds = [rbc.HiSoftBuild(code, b, b, 0, 'native probe')
                              for b in (0x5000, 0x6000, 0x7000)]
                    ssx, meta = rbc.build_ssx(builds, font, rld, 384,
                                              use_rom_font=rom_font)
                    parsed = rld.parse_ssx(ssx)
                    self.assertLess(max(len(ssx),len(parsed['image'])+
                                        parsed['bss']+parsed['stack']),12000)
                    load = 0x8000
                    image = bytearray(parsed['image'])
                    for site in parsed['relocs']:
                        ptr = int.from_bytes(image[site:site+2],'little')
                        image[site:site+2] = ((ptr+load)&65535).to_bytes(2,'little')
                    mem = bytearray(65536)
                    mem[load:load+len(image)] = image
                    for address, value in original.items():
                        mem[address] = value
                    mem[0xfc00] = 0x5a  # shell's glyph must remain untouched
                    cpu = Z80CPU(mem.__getitem__,mem.__setitem__)
                    cpu.sp=0xe000
                    cpu.pc=load
                    calls=[]
                    private_udg=None
                    ended=False
                    for _ in range(1000):
                        if cpu.pc == load + meta['entry_offset']:
                            private_udg = mem[0x5c7b] | mem[0x5c7c]<<8
                            self.assertGreaterEqual(private_udg,load)
                            self.assertIn(private_udg+UDG_BYTES-load,parsed['relocs'])
                            clean = (mem[private_udg+UDG_BYTES] |
                                     mem[private_udg+UDG_BYTES+1]<<8)
                            self.assertGreaterEqual(clean,load)
                            self.assertLess(clean,load+len(image))
                        if cpu.pc==0x6003:
                            code_no=cpu.a
                            arg=cpu.h<<8 | cpu.l
                            calls.append((code_no,arg))
                            if code_no == 1:
                                self.assertEqual(arg, status or 0)
                                ended=True
                                break
                            self.assertEqual(code_no,39)
                            self.assertIn(arg, (0,1))
                            # Return from kernel call, leaving the process state.
                            cpu.pc = mem[cpu.sp] | mem[cpu.sp+1]<<8
                            cpu.sp = (cpu.sp+2)&65535
                            continue
                        self.assertNotEqual(cpu.pc,8,'ROM RST 8 would panic the kernel')
                        cpu.step()
                    self.assertTrue(ended,'native process did not exit')
                    self.assertEqual(calls,[(39,1),(39,0),(1,status or 0)])
                    self.assertEqual(mem[private_udg],73)
                    self.assertEqual(mem[0xfc00],0x5a)
                    self.assertEqual({a:mem[a] for a in original},original)


if __name__ == '__main__':
    unittest.main()
