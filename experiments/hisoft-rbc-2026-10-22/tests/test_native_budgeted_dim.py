"""Runtime numeric DIM: native budget, ROM syntax and index isolation."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest

STAGE = Path(__file__).resolve().parents[1] / 'stage'
sys.path.insert(0, str(STAGE))
from native_dynamic_dim import with_bounded_dynamic_dims
from native_budgeted_dim import (unproved_numeric_dims, with_budgeted_numeric_dims,
                                 capacity_for_native_budget)

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


class BudgetTests(unittest.TestCase):
    def test_physical_budget_not_ssx_file_budget(self):
        cap = capacity_for_native_budget(12000, 8500, 1200, 384, 10)
        self.assertEqual(cap, 192)
        self.assertLessEqual(8500 + 1200 + 384 + (cap - 1) * 10, 12000)
        self.assertGreater(8500 + 1200 + 384 + cap * 10, 12000)
        self.assertEqual(capacity_for_native_budget(9000, 8500, 1200, 384, 10), 1)
        self.assertEqual(capacity_for_native_budget(0, 100, 100, 384, 5), 12991)
        with self.assertRaises(ValueError):
            capacity_for_native_budget(12000, 0, 0, 384, 0)

    def test_only_genuine_numeric_array_tokens(self):
        lines = [
            (10, b'\xee N:\xe9 P(N):\xe9 C(4,3)\r'),
            (20, b'\xf5 "DIM X(N)":\xea DIM Y(N)\r'),
            (30, b'\xe9 Q(N):\xe9 Z$(N)\r'),
        ]
        self.assertEqual(set(unproved_numeric_dims(lines, {})), {15, 16})
        self.assertNotIn(15, unproved_numeric_dims(lines, {15: (b'n', 3)}))

    def test_mixed_numeric_shapes_rejected(self):
        for pair in [
            [(10, b'\xe9 A(N):\xe9 A(N,3)\r')],
            [(10, b'\xe9 A(N):\xe9 A(10)\r')],
            [(10, b'\xe9 A(N*2)\r')],
            [(10, b'\xe9 A(USR 1)\r')],
        ]:
            with self.subTest(pair=pair):
                self.assertEqual(unproved_numeric_dims(pair, {}), {})


@unittest.skipUnless(READY, 'needs original 48K ROM and HiSoft compiler image')
class NativeInputDims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.img = hbcimage.Image.from_tape(TAPE)
        cls.kw = source.Keywords(cls.rom)
        cls.backend = with_budgeted_numeric_dims(
            with_bounded_dynamic_dims(compiler.Compiler, real_type=compiler.REAL,
                                      memfill_rt=compiler.RT.MEM_FILL),
            capacity=56, real_type=compiler.REAL, memfill_rt=compiler.RT.MEM_FILL)

    def compile(self, listing, kind=None):
        obj = (kind or self.backend)(self.img, self.rom)
        program = encode_strict_listing(listing)
        program = source.add_directives(program, [], True, [], self.kw, obj.fp)
        tokens = source.tokenize_directives(program, self.kw)
        return obj, obj.compile_whole(tokens), tokens

    def test_input_dims_and_redim_compiled_from_original_tokens(self):
        listing = ('10 INPUT N: DIM P(N)\n'
                   '20 FOR I=1 TO N: LET P(I)=I: NEXT I\n'
                   '30 INPUT N: DIM P(N): LET P(1)=3\n')
        c, res, tokens = self.compile(listing)
        self.assertTrue(res.ok, (res.error, res.detail))
        self.assertEqual(c._zxux_budgeted_dims, frozenset({15}))
        self.assertEqual(c.arrays[15]['last'], 56)
        self.assertEqual(c.arrays[15]['zxux_dynamic_slot'],
                         c.arrays[15]['addr'] + 56 * 5)
        self.assertEqual(self.compile(listing)[2], tokens)
        self.assertFalse(self.compile(listing, compiler.Compiler)[1].ok)

    def test_numeric_string_arrays_not_reinterpreted(self):
        listing = '10 INPUT N: DIM A$(N): DIM B(N,2)\n'
        c, res, _ = self.compile(listing)
        self.assertNotIn(0, c._zxux_budgeted_dims)
        self.assertNotIn(1, c._zxux_budgeted_dims)
        self.assertFalse(res.ok)

    def test_multi_arrays_with_shared_controller(self):
        c, res, _ = self.compile('10 INPUT LB: DIM X(LB): DIM Y(LB)\n20 PRINT X(1)+Y(1)\n')
        self.assertTrue(res.ok, (res.error, res.detail))
        self.assertEqual(c._zxux_budgeted_dims, frozenset({23,24}))

    def test_native_runtime_bound_guards(self):
        def check(kind, value, accept):
            parts = []
            class Stub:
                def emit(self, code, *args):
                    parts.extend(asm(code, *args))
                def ld_hl_ind(self, addr):
                    parts.extend(asm('ld hl,({})', addr))
            obj = with_bounded_dynamic_dims(Stub, real_type=0, memfill_rt=0)()
            if kind == 'DIM':
                obj._zxux_valid_count(56)
            else:
                obj._zxux_valid_index(0x8000)
            mem = bytearray(65536)
            machine = bytes(parts) + b'\xc9'
            mem[0x7000:0x7000+len(machine)] = machine
            mem[0x8000:0x8002] = (5).to_bytes(2, 'little')
            cpu = Z80(mem)
            cpu.hl = value
            cpu.sp = 0x9000
            cpu.hooks[8] = lambda _: (_ for _ in ()).throw(IndexError('subscript'))
            if accept:
                cpu.call(0x7000)
                self.assertEqual(cpu.hl, value)
            else:
                with self.assertRaises(IndexError):
                    cpu.call(0x7000)
        for value in (1, 5, 56): check('DIM', value, True)
        for value in (0, 57, 65535): check('DIM', value, False)
        for value in (1, 5): check('INDEX', value, True)
        for value in (0, 6, 65535): check('INDEX', value, False)


if __name__ == '__main__':
    unittest.main()
