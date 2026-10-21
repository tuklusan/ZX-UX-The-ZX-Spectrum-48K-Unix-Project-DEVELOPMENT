#!/usr/bin/env python3
"""Rebuild the ZX-UX distribution from staged inputs, replacing release/dist."""
import pathlib
import re
import shutil
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
R = pathlib.Path(__file__).resolve().parents[1]
B, S, D = R / 'build', R / 'src', R / 'dist'
sys.path.insert(0, str(S / 'zx-ux-sdk/tools'))
import osbuild, turbo_boot_build, c48build, sdkpack


def checked_dir(root):
    """Do not stage input links or special files."""
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError('Invalid build input directory: ' + str(root))
    for path in root.rglob('*'):
        mode = path.lstat().st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise RuntimeError('Unsafe build input: ' + str(path))


def main():
    argv = sys.argv[1:]
    argv = argv[1:] if argv[:1] == ['--sjasm'] else argv
    sjasm = (str(pathlib.Path(argv[0]).resolve()) if len(argv) == 1
             else shutil.which('sjasmplus') or 'sjasmplus')
    # C48 corpus is still shipped under dist; the original BASIC collection
    # now lives under src. Stage both before replacing the old distribution.
    corpus = D / 'assets/c48-src'
    bonus = S / 'bonus'
    for source in (D, corpus, bonus):
        checked_dir(source)
    for name in ('src', 'sdk', 'out', 'dist-new', 'dist-old', 'dist-stage'):
        path = B / name
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise RuntimeError('Unsafe build workspace: ' + str(path))
        if path.exists():
            shutil.rmtree(path)
    stage = B / 'dist-new'
    shutil.copytree(corpus, stage / 'assets/c48-src')
    shutil.copytree(bonus, stage / 'bonus')
    shutil.copytree(S / 'zx-ux', B / 'src')
    shutil.copytree(S / 'zx-ux-sdk', B / 'sdk')
    (B / 'out').mkdir()
    (B / 'sdk/rom').mkdir(exist_ok=True)
    for name, folder in (('48.rom', 'rom'), ('font4x8.bin', '')):
        shutil.copy2(S / 'zx-ux' / folder / name, B / 'sdk/rom' / name)
    subprocess.run([sys.executable, str(S / 'zx-ux-sdk/tools/osbuild.py'), sjasm],
                   check=True)
    syms = dict((m.group(1), int(m.group(2), 16))
                for line in (B / 'src/unix.sym').read_text().splitlines()
                if (m := re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)', line)))
    _, _, free, _ = osbuild.mkfs(syms, osbuild.program_list())
    turbo_boot_build.create_tzx(sjasm, syms, syms['kend'] - 0x6000, free,
                                output_name='ZX-UX.tzx')
    (stage / 'zx-ux').mkdir(parents=True)
    shutil.copy2(B / 'out/ZX-UX.tzx', stage / 'zx-ux/ZX-UX.tzx')
    c48build.build(B / 'sdk', stage / 'assets/c48-src', stage / 'assets/c48-bin')
    sdkpack.pack(S / 'zx-ux-sdk', S / 'zx-ux', B, stage / 'sdk/bin')
    # Publication happens only after every builder has succeeded.
    D.rename(B / 'dist-old')
    try:
        stage.rename(D)
    except BaseException:
        if not D.exists() and (B / 'dist-old').exists():
            (B / 'dist-old').rename(D)
        raise
    shutil.rmtree(B / 'dist-old')


if __name__ == '__main__':
    main()
