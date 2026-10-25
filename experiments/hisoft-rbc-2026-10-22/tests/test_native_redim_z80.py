"""Execute the emitted DIM subscript guard on an isolated Z80 CPU."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from native_redim_compiler import with_literal_redims
from z80asm import asm
from z80mini import Z80


class GuardMachine(unittest.TestCase):
    def test_compiled_guard_checks_current_shape_without_writing(self):
        class Sink:
            def __init__(self): self.asm=[]
            def emit(self, text): self.asm.append(text)
            def ld_hl_ind(self, address):
                self.asm.append(f'ld hl,(${address:04x})')
        Compiler = with_literal_redims(Sink, real_type=0, runtime_memfill=1)
        generator = Compiler()
        generator._guard_index(0x8000)
        instructions = '; '.join(generator.asm) + '; ret'
        for capacity, index, should_fail in (
                (2,0,True),(2,1,False),(2,2,False),
                (2,3,True),(1,2,True),(10,10,False),
                (10,11,True),(2,65535,True)):
            with self.subTest(capacity=capacity, index=index):
                data = bytearray(65536)
                data[0x8000:0x8002] = capacity.to_bytes(2,'little')
                guard = asm('ld hl,{}; '.format(index) + instructions)
                data[0x7000:0x7000+len(guard)] = guard
                cpu = Z80(data)
                cpu.sp = 0x9000
                cpu.hooks[8] = lambda _: (_ for _ in ()).throw(IndexError('Subscript wrong'))
                snapshot = bytes(data[0x8000:0x8004])
                if should_fail:
                    with self.assertRaises(IndexError): cpu.call(0x7000)
                else:
                    cpu.call(0x7000)
                    self.assertEqual(cpu.hl,index)
                    self.assertEqual(cpu.sp,0x9000)
                self.assertEqual(bytes(data[0x8000:0x8004]),snapshot)


if __name__=='__main__': unittest.main()
