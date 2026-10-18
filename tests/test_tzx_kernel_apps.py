"""End-to-end kernel-only RVM gate for four C48 application New commands.

No imported syscall simulator, mock filesystem or hand-built screenshots.
Runs the linked ZX-UX kernel reconstructed from its one verified TZX.
Physical turbo pulse timing is independently validated by Fuse, not here.
"""
from __future__ import annotations
import pathlib
import tempfile
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'release/dist/sdk/bin/py'))
import rvm
import rtap
import zxux
import zxscreen

APPS=('write48','sheet48','wire3d','gp82')
TZX=ROOT/'release/dist/zx-ux/ZX-UX.tzx'
BIN=ROOT/'release/dist/assets/c48-bin/ssx'


def run_app(name, keys):
    path=BIN/(name+'.ssx')
    runner=rvm.run_kernel(path,keys=keys,frames=1400)
    assert runner.fg.started is not None, name+' did not reach actual kernel loader'
    screen=zxscreen.screen_text(runner.picture()[0])
    assert runner.why in ('input','frames'), (name,runner.why)
    return screen, runner


class KernelOnlyApps(unittest.TestCase):
    def test_single_tzx_and_actual_kernel(self):
        self.assertTrue(TZX.is_file())
        self.assertFalse((TZX.parent/'ZX-UX.tap').exists())
        self.assertFalse((ROOT/'release/build/out/ZX-UX.tap').exists())
        image=zxux.SystemImage(str(TZX))
        self.assertEqual(len(image.blocks),4)
        self.assertEqual(image.merged[0x6000-0x5D98],0xc3)
        self.assertEqual(len(image.merged),len((ROOT/'release/build/out/merged-image.bin').read_bytes()))
        with self.assertRaisesRegex(zxux.RvmError,'TZX required'):
            zxux.read_tape('legacy.tap')
        with self.assertRaisesRegex(SystemExit,'TZX files only'):
            rtap.read_tape('legacy.tap')

    def test_corrupt_turbo_fails_closed(self):
        data=bytearray(TZX.read_bytes())
        # Flip a byte in the first turbo segment: packet CRC and XOR become wrong.
        pos=10
        for _ in range(4):
            self.assertEqual(data[pos],0x10)
            pos+=5+int.from_bytes(data[pos+3:pos+5],'little')
        self.assertEqual(data[pos],0x11)
        data[pos+19+30] ^= 0x01
        with tempfile.TemporaryDirectory() as d:
            dest=pathlib.Path(d)/'bad.tzx';dest.write_bytes(data)
            with self.assertRaisesRegex(zxux.RvmError,'checksum'):
                zxux.SystemImage(str(dest))

    def test_new_cancel_and_confirm(self):
        for app in APPS:
            with self.subTest(app=app):
                cancelled,_=run_app(app,'nx')
                self.assertIn('NEW CANCELLED',cancelled)
                if app=='write48':
                    self.assertIn('SIR CLIVE SINCLAIR',cancelled)
                cleared,_=run_app(app,'nY')
                self.assertIn('NEW BLANK' if app!='wire3d' else 'NEW EMPTY',cleared)
                if app=='write48':
                    self.assertNotIn('SIR CLIVE SINCLAIR',cleared)
                if app=='wire3d':
                    self.assertIn('Q Quit',cleared)
                    self.assertIn('B/P PLANE',cleared)

    def test_new_then_save_and_reload_uses_real_ram_filesystem(self):
        for app in APPS:
            with self.subTest(app=app):
                screen,r=run_app(app,'nYs{ENTER}l{ENTER}')
                self.assertGreater(r.session.syscalls,20)
                self.assertNotIn('LOAD FAILED',screen)
                if app == 'gp82':
                    # GP82's status row is overwritten by fixed help text;
                    # its zero-valued statistics prove the blank file state.
                    self.assertIn('W0',screen)
                else:
                    self.assertIn('LOADED FROM RAM',screen)

    def test_rtap_can_list_boot_and_appended_tzx(self):
        with tempfile.TemporaryDirectory() as d:
            dest=pathlib.Path(d)/'combined.tzx'
            self.assertEqual(rtap.main(['-o',str(dest),'--after',str(TZX),str(BIN/'write48.ssx')]),0)
            boot_records=rtap.read_tape(str(TZX))
            self.assertEqual(len(boot_records),4)  # ROM bootstrap standard records
            records=rtap.read_tape(str(dest))
            self.assertEqual(records[:len(boot_records)],boot_records)
            self.assertEqual(len(records),6)  # four boot plus header and SSX data
            self.assertIn('program  /dev/cassette/write48', '\n'.join(rtap.list_blocks(records)))
            data=dest.read_bytes()
            # A truncated turbo-record payload must never be accepted.
            first_turbo=10
            for _ in range(4):
                self.assertEqual(data[first_turbo],0x10)
                first_turbo+=5+int.from_bytes(data[first_turbo+3:first_turbo+5],'little')
            self.assertEqual(data[first_turbo],0x11)
            with self.assertRaisesRegex(SystemExit,'truncated turbo TZX header'):
                rtap.tzx_blocks(data[:first_turbo+18])
            with self.assertRaisesRegex(SystemExit,'truncated turbo TZX payload'):
                rtap.tzx_blocks(data[:first_turbo+19])

    def test_turbo_tzx_can_be_extended_with_app_tape(self):
        with tempfile.TemporaryDirectory() as d:
            dest=pathlib.Path(d)/'combined.tzx'
            self.assertEqual(rtap.main(['-o',str(dest),'--after',str(TZX),str(BIN/'write48.ssx')]),0)
            self.assertTrue(dest.read_bytes().startswith(TZX.read_bytes()))
            self.assertGreater(dest.stat().st_size,TZX.stat().st_size)
            with self.assertRaises(SystemExit):
                rtap.write(str(pathlib.Path(d)/'bad.tap'),b'',[])

if __name__=='__main__': unittest.main()
