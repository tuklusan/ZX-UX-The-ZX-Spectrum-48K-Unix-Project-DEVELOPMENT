"""Execute the actual generated native guard against real Z80 instructions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from spectrum_runtime import guarded_val_bytes


class SpectrumRuntime(unittest.TestCase):
    def evaluate_path(self, value):
        from z80mini import Z80
        mem = bytearray(65536)
        code = guarded_val_bytes()
        mem[0x8000:0x8000+len(code)] = code
        mem[0x9000:0x9000+len(value)] = value
        descriptor = b'\0\0\x90' + len(value).to_bytes(2, 'little')
        mem[0x9200:0x9205] = descriptor
        mem[0x5c65:0x5c67] = (0x9205).to_bytes(2,'little')
        cpu = Z80(mem)
        cpu.sp = 0xe000
        cpu.pc = 0x8000
        for _ in range(300):
            if cpu.pc in (0x35de, 0x0008):
                return cpu.pc, cpu
            cpu.step()
        self.fail('native VAL guard did not terminate or enter ROM')

    def test_sinclair_literal_go_to_uses_next_existing_line(self):
        from spectrum_runtime import resolve_literal_line
        lines=[(10,b''),(220,b''),(900,b'')]
        self.assertEqual(resolve_literal_line(lines,200),220)
        self.assertEqual(resolve_literal_line(lines,220),220)
        self.assertEqual(resolve_literal_line(lines,0),10)
        self.assertEqual(resolve_literal_line(lines,901),901)
        self.assertEqual(resolve_literal_line(lines,10000),10000)

    def test_valid_runtime_expression_enter_rom(self):
        target,cpu=self.evaluate_path(b'2+3')
        self.assertEqual(target,0x35de)
        self.assertEqual(cpu.b,0x1d)
        self.assertEqual(cpu.sp,0xe000)

    def test_executable_usr_never_reaches_rom(self):
        target,cpu=self.evaluate_path(b'1+'+bytes([0xc0])+b' 32768')
        self.assertEqual(target,0x0008)
        # RST 8 pushes its own return address; the entry guard restored
        # every saved register before entering Spectrum error dispatch.
        self.assertEqual(cpu.sp,0xdffe)

    def test_nested_evaluation_never_bypasses_usr_guard(self):
        for token in (0xb0,0xae):
            with self.subTest(token=token):
                self.assertEqual(self.evaluate_path(bytes([token,0xc0]))[0],0x0008)

    def test_quoted_nonexecuted_usr_is_not_rejected(self):
        self.assertEqual(self.evaluate_path(b'"'+bytes([0xc0])+b'"')[0],0x35de)

    def test_rem_nonexecuted_usr_is_not_rejected(self):
        self.assertEqual(self.evaluate_path(b'1'+bytes([0xea,0xc0]))[0],0x35de)

    def test_empty_dynamic_expression_reaches_rom_error_handler(self):
        self.assertEqual(self.evaluate_path(b'')[0],0x35de)

if __name__=='__main__':unittest.main()