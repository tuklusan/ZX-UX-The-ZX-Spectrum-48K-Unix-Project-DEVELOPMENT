"""ZX-UX validation description."""
from __future__ import annotations
import os
import sys
from pathlib import Path
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from native_dynamic_string_dim import _proved_string_lengths, with_bounded_string_dims
from native_dynamic_dim import with_bounded_dynamic_dims

FRONTEND = Path(os.environ['RBC_TEST_FRONTEND']) if 'RBC_TEST_FRONTEND' in os.environ else None
TAPE = Path(os.environ['RBC_TEST_HISOFT_TAPE']) if 'RBC_TEST_HISOFT_TAPE' in os.environ else None
ROM = Path(os.environ['RBC_TEST_ROM']) if 'RBC_TEST_ROM' in os.environ else None
READY = bool(FRONTEND and (FRONTEND / 'compiler.py').is_file()
             and TAPE and TAPE.is_file() and ROM and ROM.is_file())
if READY:
    sys.path.insert(0, str(FRONTEND))
    import compiler, hbcimage, source, tap
    from basic_listing import encode_strict_listing
    from z80asm import asm
    from z80mini import Z80


class BoundSyntaxTests(unittest.TestCase):
    def test_literals_and_unrelated_dim_remain_independent(self):
        # Simulate just the preserved token stream for token-focused proof.
        # Numeric DIM is irrelevant; string bounds come from LET controls.
        lines = [(10, b'\xf1 N=5: \xe9 A$(N): \xe9 B(100)\r')]
        self.assertEqual(_proved_string_lengths(lines), {0: (b'n', 5)})

    def test_unbounded_input_and_strings_do_not_make_bounds(self):
        lines = [(10, b'\xee N: \xe9 A$(N)\r')]
        self.assertEqual(_proved_string_lengths(lines), {})
        lines = [(10, b'\xf5 "DIM A$(N)": \xea DIM A$(N)\r')]
        self.assertEqual(_proved_string_lengths(lines), {})


@unittest.skipUnless(READY, 'requires HiSoft v1.1 image and original Spectrum ROM')
class OriginalRomNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.img = hbcimage.Image.from_tape(TAPE)
        assert cls.img.v11
        cls.kw = source.Keywords(cls.rom)
        cls.backend = with_bounded_string_dims(
            with_bounded_dynamic_dims(compiler.Compiler,
                                      real_type=compiler.REAL,
                                      memfill_rt=compiler.RT.MEM_FILL),
            string_type=compiler.STRING, memfill_rt=compiler.RT.MEM_FILL)

    def compile(self, listing, native=True):
        obj = (self.backend if native else compiler.Compiler)(self.img, self.rom)
        program = encode_strict_listing(listing)
        program = source.add_directives(program, [], True, [], self.kw, obj.fp)
        original = source.tokenize_directives(program, self.kw)
        result = obj.compile_whole(original)
        return obj, result, original

    def test_repeated_runtime_dim_and_slices(self):
        listing = ('10 LET N=3: DIM A$(N)\n'
                   '20 LET A$="ABC": PRINT A$(2 TO 3)\n'
                   '30 LET N=5: DIM A$(N): PRINT LEN A$\n')
        c, res, tokens = self.compile(listing)
        self.assertTrue(res.ok, (res.error, res.detail))
        self.assertEqual(c._zxux_dynamic_string_dims, {0: (b'n', 5)})
        self.assertEqual(c.strvars[0]['last'], 5)
        self.assertEqual(c.strvars[0]['first'], 0)
        self.assertEqual(c.var_bytes, 12)  # 5-byte N plus 2+5-byte A$
        self.assertEqual(self.compile(listing)[2], tokens)
        self.assertFalse(self.compile(listing, native=False)[1].ok)

    def test_arithmetic_and_multiletter_controller(self):
        c, res, _ = self.compile('10 LET LB=7: LET K=2: DIM B$(LB+K)\n20 PRINT LEN B$\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        self.assertEqual(c.strvars[1]['last'], 9)

    def test_input_dimensions_still_fail_closed(self):
        _, res, _ = self.compile('10 INPUT N: DIM A$(N)\n20 PRINT LEN A$\n')
        self.assertFalse(res.ok)

    def test_full_array_not_mistaken_for_single_string(self):
        c, res, _ = self.compile('10 LET N=4: DIM A$(N,3)\n')
        self.assertFalse(res.ok)
        self.assertEqual(c._zxux_dynamic_string_dims, {})

    def test_guard_executes_without_out_of_bounds_writes(self):
        chunks = []
        class Stub:
            def emit(self, code, *args):
                chunks.extend(asm(code, *args))
        guard = with_bounded_string_dims(Stub, string_type=0, memfill_rt=0)()
        guard._zxux_bound_guard(5)
        code = bytes(chunks) + b'\xc9'
        for size in (1, 3, 5):
            mem = bytearray(65536)
            mem[0x7100:0x7100+len(code)] = code
            cpu = Z80(mem)
            cpu.hl = size; cpu.sp = 0x9000
            cpu.hooks[8] = lambda _: (_ for _ in ()).throw(IndexError('DIM length'))
            cpu.call(0x7100)
            self.assertEqual(cpu.hl, size)
        for size in (0, 6, 65535):
            mem = bytearray(65536)
            mem[0x7100:0x7100+len(code)] = code
            cpu = Z80(mem)
            cpu.hl = size; cpu.sp = 0x9000
            cpu.hooks[8] = lambda _: (_ for _ in ()).throw(IndexError('DIM length'))
            with self.assertRaises(IndexError, msg=str(size)):
                cpu.call(0x7100)

if __name__ == '__main__':
    unittest.main()
