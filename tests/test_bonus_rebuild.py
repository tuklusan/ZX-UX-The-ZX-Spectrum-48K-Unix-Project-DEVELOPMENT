#!/usr/bin/env python3
"""Exercise the real dist replacement script with lightweight build stubs."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / 'release/build/build.py'


class BonusRebuildChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = self.root / 'release'
        self.dist = self.release / 'dist'
        self.source = self.release / 'src'
        self.tools = self.source / 'zx-ux-sdk/tools'
        self.tools.mkdir(parents=True)
        kernel = self.source / 'zx-ux'
        (kernel / 'rom').mkdir(parents=True)
        (kernel / 'rom/48.rom').write_bytes(b'rom')
        (kernel / 'font4x8.bin').write_bytes(b'font')
        (self.release / 'build').mkdir()
        (self.dist / 'assets/c48-src').mkdir(parents=True)
        (self.dist / 'assets/c48-src/hello.c').write_bytes(b'int main(void) { return 0; }\n')
        (self.release / 'build/build.py').write_bytes(BUILD_SCRIPT.read_bytes())
        (self.tools / 'osbuild.py').write_text('''
from pathlib import Path
R = Path(__file__).resolve().parents[3]
def mkfs(syms, programs): return None, None, 1024, None
def program_list(): return []
if __name__ == '__main__':
    (R / 'build/src/unix.sym').write_text('kend: EQU 0x7000\\n')
''')
        (self.tools / 'turbo_boot_build.py').write_text('''
from pathlib import Path
def create_tzx(*args, **kwargs):
    (Path(__file__).resolve().parents[3] / 'build/out/ZX-UX.tzx').write_bytes(b'tape')
''')
        (self.tools / 'c48build.py').write_text('''
def build(*args):
    args[2].mkdir(parents=True, exist_ok=True)
    (args[2] / 'compiled.bin').write_bytes(b'executable')
''')
        (self.tools / 'sdkpack.py').write_text('''
def pack(*args):
    args[-1].mkdir(parents=True, exist_ok=True)
    (args[-1] / 'rcc').write_text('sdk')
''')

    def rebuild(self, succeeds=True):
        result = subprocess.run([sys.executable, '-B',
                                 str(self.release / 'build/build.py')],
                                capture_output=True, text=True)
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stderr)
        return result

    def test_repeated_rebuild_keeps_bonus_files_byte_for_byte(self):
        bonus = self.dist / 'bonus/60-programs/01-minelay'
        files = {'BASIC/01-minelay.bas': b'10 PRINT "HELLO"\r\n',
                 'BASIC/01-minelay.tzx': b'\x00\xff\x01',
                 'BASIC/SCREENSHOTS/01-INTRO.png': b'\x89PNG\r\n\x1a\n\0',
                 'C48/src/minelay.c': b'int main(void) { return 0; }\n',
                 'C48/bin/ssx/minelay.ssx': b'\0SSX\xff',
                 'C48/bin/tzx/minelay.tzx': b'ZXTape!\x1a',
                 'C48/screenshots/rvm/start.png': b'RVM\0',
                 'C48/screenshots/fuse/start.png': b'FUSE\0'}
        for relative, content in files.items():
            path = bonus / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        other = self.dist / 'bonus/notes.txt'
        other.write_bytes(b'other bonus data\n')
        baseline = {str(path.relative_to(self.dist)): hashlib.sha256(path.read_bytes()).digest()
                    for path in (self.dist / 'bonus').rglob('*') if path.is_file()}
        self.rebuild()
        self.rebuild()
        after = {str(path.relative_to(self.dist)): hashlib.sha256(path.read_bytes()).digest()
                 for path in (self.dist / 'bonus').rglob('*') if path.is_file()}
        self.assertEqual(after, baseline)
        self.assertTrue((self.dist / 'assets/c48-bin/compiled.bin').is_file())
        self.assertTrue((self.dist / 'zx-ux/ZX-UX.tzx').is_file())
        self.assertTrue((self.dist / 'sdk/bin/rcc').is_file())
        self.assertEqual((self.dist / 'assets/c48-src/hello.c').read_bytes(),
                         b'int main(void) { return 0; }\n')

    def test_rejects_links_before_replacing_existing_dist(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'private.txt').write_bytes(b'do not copy')
        bonus = self.dist / 'bonus/60-programs/01-minelay/C48/src'
        bonus.mkdir(parents=True)
        (bonus / 'escape').symlink_to(outside, target_is_directory=True)
        original = self.dist / 'assets/c48-src/hello.c'
        self.rebuild(succeeds=False)
        self.assertTrue((bonus / 'escape').is_symlink())
        self.assertEqual(original.read_bytes(), b'int main(void) { return 0; }\n')
        self.assertFalse((self.release / 'build/dist-new').exists())

    def test_rejects_linked_bonus_root(self):
        outside = self.root / 'elsewhere'
        outside.mkdir()
        (outside / 'private.txt').write_text('keep')
        (self.dist / 'bonus').symlink_to(outside, target_is_directory=True)
        self.rebuild(succeeds=False)
        self.assertTrue((self.dist / 'bonus').is_symlink())
        self.assertTrue((outside / 'private.txt').is_file())


if __name__ == '__main__':
    unittest.main()
