"""Z80 shadow register apostrophes must not be mistaken for string quotes."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'stage'),
                str(ROOT / 'src/zx-ux-sdk')]
import ras
import rld
from z80_python.cpu import Z80CPU
from symbolic_z80 import (_canonical_source_line, _check_optimizer_output,
                          _check_protected)
from gate8_typed_cfg_liveness import inspect_typed_cfg_liveness
from gate8_native_whole_optimizer import verify_whole_optimizer_candidate

SOURCE = ("    section text\n    global start\nstart:\n"
          "    ex af,af' ; switch the alternate flags\n"
          "    ex af,af'\n    ret\n")


class ShadowRegisterQuotationTests(unittest.TestCase):
    def test_typed_cfg_and_native_assembly_preserve_prime_register(self):
        _check_optimizer_output(SOURCE)
        _check_protected(SOURCE, SOURCE, {'start'})
        self.assertEqual(
            _canonical_source_line("  EX AF,AF' ; comment ' unfinished",
                                   strip_comment=True),
            "ex af,af'")
        cfg = inspect_typed_cfg_liveness(SOURCE)
        self.assertEqual(cfg['instruction_count'], 3)
        self.assertEqual(cfg['unresolved_control_edges'], 0)
        self.assertFalse(cfg['rewrite_safe_to_admit'])
        obj = ras.assemble_text(SOURCE, 'shadow-register.s')
        ssx, *_ = rld.link([rld.Obj(obj, 'shadow-register.sso')], [],
                           entry='start', stack=384)
        info = rld.parse_ssx(ssx)
        self.assertEqual(info['image'], b'\x08\x08\xc9')
        report = verify_whole_optimizer_candidate(SOURCE, ssx,
                                                    lambda text: text)
        self.assertTrue(report['candidate_byte_identical'])
        self.assertFalse(report['optimizer_candidate_admitted_for_publication'])
        for base in (0x6000, 0x7000, 0x8000):
            with self.subTest(base=base):
                memory = bytearray(65536)
                code = rld.relocate(info['image'], info['relocs'], base)
                memory[base:base + len(code)] = code
                memory[0xd000:0xd002] = (0xb000).to_bytes(2, 'little')
                cpu = Z80CPU(memory.__getitem__, memory.__setitem__)
                cpu.a, cpu.pc, cpu.sp = 0x42, base + info['entry'], 0xd000
                for _ in range(3):
                    cpu.step()
                self.assertEqual((cpu.a, cpu.pc, cpu.sp),
                                 (0x42, 0xb000, 0xd002))


if __name__ == '__main__':
    unittest.main()
