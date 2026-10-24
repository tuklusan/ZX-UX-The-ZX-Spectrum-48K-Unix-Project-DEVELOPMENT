"""Executable native SSX entry/return checks for process-owned 48K fonts."""
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/zx-ux-sdk'))
sys.path.insert(0, str(ROOT / 'build/tmp/rbc-round2/current/rbc'))
sys.path.insert(0, str(ROOT / 'build/tmp/rbc-round2/upstream'))


class NativeFontLink(unittest.TestCase):
    def test_real_ssx_preserves_shell_font_and_restore_controls(self):
        import rbc
        import rld
        from z80mini import Z80, Z80Error
        # A tiny real Z80 entry writes a print attribute, then returns.
        # HiSoft's native wrapper must restore the complete original state.
        code = bytes.fromhex('3e 22 32 8d 5c c9')
        builds = [rbc.HiSoftBuild(code, b, b, 0, 'fixture')
                  for b in (0x5000, 0x6000, 0x7000)]
        font = bytes((i * 13) & 255 for i in range(768))
        binary, metadata = rbc.build_ssx(builds, font, rld, 384, use_rom_font=False)
        parsed = rld.parse_ssx(binary)
        self.assertTrue(binary.startswith(b'SSX1'))
        self.assertEqual(metadata['font_bytes'], 1024)
        self.assertEqual(parsed['stack'], 384)
        self.assertEqual(parsed['bss'], 0)
        self.assertEqual(metadata['entry_offset'], 156)
        load = 0x8000
        image = bytearray(parsed['image'])
        for offset in parsed['relocs']:
            original = int.from_bytes(image[offset:offset+2], 'little')
            image[offset:offset+2] = ((original+load)&65535).to_bytes(2,'little')
        mem = bytearray(65536)
        mem[load:load+len(image)] = image
        originals = {0x5c36:0, 0x5c37:0x3c, 0x5c7b:0,0x5c7c:0xfd,
                     0x5c8d:0x48,0x5c8e:0x72,0x5c8f:0x4d,0x5c90:0x16,
                     0x5c6a:0xbb,0x5c39:0x34}
        for addr, value in originals.items():
            mem[addr] = value
        cpu = Z80(mem)
        cpu.sp = 0xe000
        cpu.pc = load
        calls = []
        cpu.hooks[0x6003] = lambda c: calls.append((c.a,c.hl))
        changed_private = False
        for step in range(300):
            if cpu.pc == load + metadata['entry_offset']:
                actual_ptr = mem[0x5c36] | mem[0x5c37]<<8
                self.assertGreaterEqual(actual_ptr, load)
                font_base = actual_ptr + 256
                self.assertEqual(mem[font_base:font_base+768], font)
                mem[font_base+8*35+4] = 0xaa
                changed_private = True
            try:
                cpu.step()
            except Z80Error as exc:
                self.assertIn('HALT', str(exc))
                break
        else:
            self.fail('SSX entry never returned to the shell')
        self.assertTrue(changed_private)
        self.assertEqual([(a) for a,_ in calls], [39,39,1])
        for address, value in originals.items():
            self.assertEqual(mem[address],value, f'global system variable {address}')
        # The ZX-UX shell's physical font is not part of this process image.
        self.assertEqual(mem[0x3d00:0x3d08], bytes(8))


if __name__ == '__main__':
    unittest.main()
