#!/usr/bin/env python3
"""Prove the release rebuild updates only owned outputs, without replacing dist."""
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        self.assertEqual(result.returncode == 0, succeeds, result.stderr)
        return result

    def bonus_content(self):
        bonus = self.dist / 'bonus/60-programs/01-minelay'
        files = {'BASIC/01-minelay.bas': b'10 PRINT "HELLO"\r\n',
                 'BASIC/01-minelay.tzx': b'\x00\xff\x01',
                 'BASIC/SCREENSHOTS/01-INTRO.png': b'\x89PNG\r\n\x1a\n\0',
                 'C48/src/.gitkeep': b'',
                 'C48/bin/ssx/.gitkeep': b'',
                 'C48/bin/tzx/.gitkeep': b'',
                 'C48/screenshots/rvm/.gitkeep': b'',
                 'C48/screenshots/fuse/.gitkeep': b''}
        for relative, contents in files.items():
            path = bonus / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        (self.dist / 'bonus/notes.txt').write_bytes(b'other bonus data\n')
        return {str(p.relative_to(self.dist)): hashlib.sha256(p.read_bytes()).digest()
                for p in (self.dist / 'bonus').rglob('*') if p.is_file()}

    def test_twice_preserves_directory_identity_and_all_unrelated_files(self):
        before = self.bonus_content()
        (self.dist / 'sdk/bin').mkdir(parents=True)
        (self.dist / 'sdk/bin/user-tool').write_text('leave alone')
        (self.dist / 'assets/c48-bin').mkdir(parents=True)
        (self.dist / 'assets/c48-bin/custom.dat').write_bytes(b'leave alone')
        (self.dist / 'keep.txt').write_bytes(b'permanent')
        old = self.dist.stat().st_ino
        self.rebuild()
        self.assertEqual(self.dist.stat().st_ino, old)
        self.assertEqual((self.dist / 'assets/c48-bin/compiled.bin').read_bytes(), b'executable')
        self.assertEqual((self.dist / 'zx-ux/ZX-UX.tzx').read_bytes(), b'tape')
        self.assertEqual((self.dist / 'sdk/bin/rcc').read_text(), 'sdk')
        (self.tools / 'c48build.py').write_text((self.tools / 'c48build.py').read_text()
              .replace("b'executable'", "b'updated'"))
        self.rebuild()
        self.assertEqual((self.dist / 'assets/c48-bin/compiled.bin').read_bytes(), b'updated')
        self.assertEqual(self.dist.stat().st_ino, old)
        self.assertEqual((self.dist / 'sdk/bin/user-tool').read_text(), 'leave alone')
        self.assertEqual((self.dist / 'assets/c48-bin/custom.dat').read_bytes(), b'leave alone')
        self.assertEqual((self.dist / 'keep.txt').read_bytes(), b'permanent')
        self.assertEqual(before, {str(p.relative_to(self.dist)): hashlib.sha256(p.read_bytes()).digest()
                                  for p in (self.dist / 'bonus').rglob('*') if p.is_file()})

    def test_failed_build_leaves_existing_outputs_untouched(self):
        self.bonus_content()
        self.rebuild()
        old = {p.relative_to(self.dist): p.read_bytes() for p in self.dist.rglob('*') if p.is_file()}
        inode = self.dist.stat().st_ino
        (self.tools / 'c48build.py').write_text('def build(*args): raise RuntimeError("fail")\n')
        self.rebuild(succeeds=False)
        self.assertEqual(inode, self.dist.stat().st_ino)
        self.assertEqual(old, {p.relative_to(self.dist): p.read_bytes()
                               for p in self.dist.rglob('*') if p.is_file()})

    def test_user_changed_output_rejected_before_any_update(self):
        self.rebuild()
        changed = self.dist / 'sdk/bin/rcc'
        changed.write_bytes(b'user-managed')
        (self.tools / 'c48build.py').write_text('''
def build(*args):
    args[2].mkdir(parents=True, exist_ok=True)
    (args[2] / 'compiled.bin').write_bytes(b'new-version')
''')
        self.rebuild(succeeds=False)
        self.assertEqual(changed.read_bytes(), b'user-managed')
        self.assertEqual((self.dist / 'assets/c48-bin/compiled.bin').read_bytes(), b'executable')

    def test_new_output_collision_not_owned_is_rejected(self):
        p = self.dist / 'sdk/bin/rcc'
        p.parent.mkdir(parents=True)
        p.write_bytes(b'personal file')
        self.rebuild(succeeds=False)
        self.assertEqual(p.read_bytes(), b'personal file')

    def test_rejects_symlink_in_dist_and_does_not_follow(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'private.txt').write_bytes(b'do not copy')
        bonus = self.dist / 'bonus/60-programs/01-minelay/C48/src'
        bonus.mkdir(parents=True)
        (bonus / 'escape').symlink_to(outside, target_is_directory=True)
        self.rebuild(succeeds=False)
        self.assertEqual((outside / 'private.txt').read_bytes(), b'do not copy')
        self.assertFalse((self.release / 'build/dist-stage').exists())

    def test_rejects_linked_bonus_root_and_generated_destination(self):
        outside = self.root / 'elsewhere'
        outside.mkdir()
        (outside / 'private.txt').write_text('keep')
        (self.dist / 'bonus').symlink_to(outside, target_is_directory=True)
        self.rebuild(succeeds=False)
        (self.dist / 'bonus').unlink()
        (self.dist / 'sdk/bin').mkdir(parents=True)
        (self.dist / 'sdk/bin/rcc').symlink_to(outside / 'private.txt')
        self.rebuild(succeeds=False)
        self.assertEqual((outside / 'private.txt').read_text(), 'keep')

    def test_install_failure_rolls_back_files_and_manifest(self):
        self.rebuild()
        loader = importlib.util.spec_from_file_location('build_under_test', BUILD_SCRIPT)
        module = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(module)
        # The module's paths are set by its checked-in source; test publication
        # on that module's real interface using paths under this temp release.
        module.D = self.dist
        module.R = self.release
        stage = self.root / 'stage'
        for relative, contents in [('assets/c48-bin/compiled.bin', b'new'),
                                   ('sdk/bin/rcc', b'new'),
                                   ('zx-ux/ZX-UX.tzx', b'new')]:
            p = stage / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(contents)
        original = {p.relative_to(self.dist): p.read_bytes() for p in self.dist.rglob('*') if p.is_file()}
        replace = module.os.replace
        calls = [0]
        def fail_third(src, dst):
            calls[0] += 1
            if calls[0] == 3:
                raise OSError('injected write failure')
            return replace(src, dst)
        with mock.patch.object(module.os, 'replace', side_effect=fail_third):
            with self.assertRaises(OSError):
                module.install(stage)
        self.assertEqual(original, {p.relative_to(self.dist): p.read_bytes()
                                   for p in self.dist.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
