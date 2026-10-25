"""Native, process-safe replacement for deadlocking ROM pagination."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / 'stage' / 'native_auto_scroll.py'
sys.path.insert(0, str(SRC.parent))
from native_auto_scroll import with_native_screen_scroll, SCR_CT


class CompilerWrapperTests(unittest.TestCase):
    def test_print_only_emits_balanced_save_restore(self):
        class Base:
            def __init__(self):
                self.parts = []
            def emit(self, text):
                self.parts.append(text)
            def st_print(self):
                self.parts.append('original PRINT')
            def st_let(self):
                self.parts.append('original LET')
        instance = with_native_screen_scroll(Base)()
        instance.st_let()
        self.assertEqual(instance.parts, ['original LET'])
        instance.st_print()
        self.assertEqual(instance.parts[1:], [
            'ld a,(23692); push af; ld a,255; ld (23692),a',
            'original PRINT', 'pop af; ld (23692),a'])

    def test_wrapping_can_preserve_unmodified_base_methods(self):
        class Base:
            def __init__(self):
                self.calls = 0
                self.emitted = []
            def emit(self, text): self.emitted.append(text)
            def st_print(self): self.calls += 1
        wrapped = with_native_screen_scroll(Base)
        c = wrapped()
        c.st_print()
        self.assertEqual(c.calls, 1)
        self.assertEqual(len(c.emitted), 2)
        self.assertEqual(SCR_CT, 0x5C8C)

    def test_z80_counter_restore_and_original_stack(self):
        upstream = os.environ.get('RBC_TEST_FRONTEND')
        if not upstream:
            self.skipTest('RBC_TEST_FRONTEND not supplied')
        sys.path.insert(0, upstream)
        from z80asm import asm
        from z80mini import Z80
        # The native PRINT may use the ROM counter internally, but the
        # process-visible value and caller's SP must survive the call.
        instructions = ('ld a,(23692); push af; ld a,255; ld (23692),a; '
                        'ld a,(23692); dec a; ld (23692),a; '
                        'pop af; ld (23692),a; ret')
        code = asm(instructions)
        for original in (0, 1, 22, 255):
            mem = bytearray(65536)
            mem[0x7200:0x7200+len(code)] = code
            mem[SCR_CT] = original
            cpu = Z80(mem)
            cpu.sp = 0x9000
            cpu.call(0x7200)
            self.assertEqual(mem[SCR_CT], original)
            self.assertEqual(cpu.sp, 0x9000)


class OriginalNativeRuntimeTests(unittest.TestCase):
    def test_drag_racer_advances_beyond_scroll_and_reads_key(self):
        required = [os.environ.get(k) for k in ('RBC_TEST_FRONTEND',
                   'RBC_TEST_HISOFT_TAPE','RBC_TEST_ROM','RBC_TEST_SDK',
                   'RBC_TEST_RBC','RBC_TEST_SYSTEM')]
        if not all(required):
            self.skipTest('native RBC + verified ZX-UX system test environment absent')
        repo = Path(__file__).resolve().parents[3]
        src = Path(os.environ.get('RBC_TEST_DRAG_RACER',
              repo/'src/bonus/60-programs/49-drag-racer/BASIC/49-drag-racer.bas'))
        self.assertTrue(src.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'49-drag-racer.ssx'
            cmd = [sys.executable,os.environ['RBC_TEST_RBC'],str(src),
                   '--frontend',required[0],'--tape',required[1],
                   '--rom',required[2],'--sdk',required[3],'-o',str(dest)]
            result = subprocess.run(cmd, text=True, capture_output=True,
                                    timeout=80)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(dest.stat().st_size, 12000)
            sys.path.insert(0,str(Path(required[3])))
            from rvm import Options, Runner
            opt = Options()
            opt.prog = str(dest)
            opt.system = required[5]
            opt.cache = True
            opt.headless = True
            opt.mute = True
            r=Runner(opt)
            r.start()
            scroll_prompt = [0]
            def entered_rom_wait(m):
                scroll_prompt[0] += 1
                return False
            r.session.m.hooks[0x15D4] = entered_rom_wait
            for _ in range(1100): r.frame()
            self.assertIsNotNone(r.fg.started)
            self.assertIsNone(r.fg.ended)
            self.assertEqual(scroll_prompt[0], 0,
                             'ROM WAIT-KEY still deadlocks on scroll prompt')
            before=r.picture()[0]
            r.session.kb.add([('press', ('a',), 10)])
            for _ in range(700): r.frame()
            self.assertEqual(scroll_prompt[0], 0)
            self.assertIsNone(r.fg.ended)
            self.assertNotEqual(before, r.picture()[0],
                                'game must respond after instruction screen')

if __name__=='__main__':
    unittest.main()
