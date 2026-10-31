#!/usr/bin/env python3
"""Rebuild dist/ from sources within this portable developer directory."""
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
import osbuild, turbo_boot_build, c48build, sdkpack, basicpack, forthbuild, pascalpack, fortranpack, rb2ctpack

FORTH_SHOWCASE_DIRS = ('numerical-analysis', 'portable', 'ported')


def checked_dir(root):
    """Do not stage input links or special files."""
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError('Invalid build input directory: ' + str(root))
    for path in root.rglob('*'):
        mode = path.lstat().st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise RuntimeError('Unsafe build input: ' + str(path))



def copy_original_programs(source, destination, no_cache):
    """Stage only the 60 BASIC program folders and the social preview PNG.

    The source collection retains its historical metadata, tools and archives;
    those top-level items are not release payloads.
    """
    collection = source / '60-programs'
    output = destination / '60-programs'
    program_dirs = sorted(p for p in collection.iterdir()
                          if p.is_dir() and re.fullmatch(r'\d{2}-.+', p.name))
    if [int(p.name[:2]) for p in program_dirs] != list(range(1, 61)):
        raise RuntimeError('Expected exactly 60 numbered BASIC program directories')
    preview = collection / 'sixty-programs-social-preview.png'
    if not preview.is_file() or preview.is_symlink():
        raise RuntimeError('Missing or unsafe BASIC social preview: ' + str(preview))
    output.mkdir(parents=True)
    for program in program_dirs:
        # The separately packaged RB2CT hand ports never enter BASIC archives.
        def no_port(folder, names):
            ignored = set(no_cache(folder, names))
            if pathlib.Path(folder) == program:
                ignored.add('C48')
            return ignored
        shutil.copytree(program, output / program.name, ignore=no_port)
    shutil.copy2(preview, output / preview.name)


def copy_forth_showcase(source, destination, no_cache):
    """Stage only the genuine Forth demonstration collections."""
    source = pathlib.Path(source)
    destination = pathlib.Path(destination)
    destination.mkdir(parents=True)
    for name in FORTH_SHOWCASE_DIRS:
        folder = source / name
        if folder.is_symlink() or not folder.is_dir():
            raise RuntimeError('Missing Forth showcase directory: ' + str(folder))
        shutil.copytree(folder, destination / name, ignore=no_cache)


def preserve_existing_c48_release(old_dist, stage):
    """Retain existing genuine C48 emulator captures during staged builds."""
    if not old_dist.is_dir():
        return
    for branch in ('screenshots/c48/rvm', 'screenshots/c48/fuse'):
        old = old_dist / branch
        if not old.is_dir():
            continue
        for src in old.rglob('*'):
            if not src.is_file():
                continue
            rel = src.relative_to(old)
            if 'basic' in rel.parts:
                continue  # The old RBC galleries are not C48 programs.
            dst = stage / branch / rel
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)



def main():
    argv = sys.argv[1:]
    argv = argv[1:] if argv[:1] == ['--sjasm'] else argv
    sjasm = (str(pathlib.Path(argv[0]).resolve()) if len(argv) == 1
             else shutil.which('sjasmplus') or 'sjasmplus')
    # Both source collections are independent of disposable dist/.
    corpus = S / 'assets/c48-src'
    originals = S / 'assets/basic-src/original-sinclair-basic-collections'
    docs = S / 'docs'
    for source in (corpus, originals, docs):
        checked_dir(source)
    if D.exists() or D.is_symlink():
        checked_dir(D)
    for name in ('src', 'sdk', 'out', 'dist-new', 'dist-old', 'dist-stage'):
        path = B / name
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise RuntimeError('Unsafe build workspace: ' + str(path))
        if path.exists():
            shutil.rmtree(path)
    stage = B / 'dist-new'
    # Python cache files are never source inputs or release deliverables.
    no_cache = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
    shutil.copytree(corpus, stage / 'assets/c48-src', ignore=no_cache)
    copy_original_programs(originals, stage / 'bonus', no_cache)
    preserve_existing_c48_release(D, stage)
    basicpack.package(S, stage)
    checked_dir(S / 'assets/forth-src')
    copy_forth_showcase(S / 'assets/forth-src', stage / 'assets/forth-src', no_cache)
    pascalpack.package(S, stage)
    shutil.copytree(S / 'zx-ux', B / 'src', ignore=no_cache)
    shutil.copytree(S / 'zx-ux-sdk', B / 'sdk', ignore=no_cache)
    (B / 'out').mkdir()
    (B / 'sdk/rom').mkdir(exist_ok=True)
    for name, folder in (('48.rom', 'rom'), ('font4x8.bin', '')):
        shutil.copy2(S / 'zx-ux' / folder / name, B / 'sdk/rom' / name)
    subprocess.run([sys.executable, '-B', str(S / 'zx-ux-sdk/tools/osbuild.py'), sjasm],
                   check=True)
    syms = dict((m.group(1), int(m.group(2), 16))
                for line in (B / 'src/unix.sym').read_text().splitlines()
                if (m := re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)', line)))
    _, _, free, _ = osbuild.mkfs(syms, osbuild.program_list())
    turbo_boot_build.create_tzx(sjasm, syms, syms['kend'] - 0x6000, free,
                                output_name='ZX-UX.tzx')
    (stage / 'zx-ux/tzx').mkdir(parents=True)
    shutil.copy2(B / 'out/ZX-UX.tzx', stage / 'zx-ux/tzx/ZX-UX.tzx')
    c48build.build(B / 'sdk', stage / 'assets/c48-src', stage / 'assets/c48-bin')
    rb2ctpack.package(stage)
    forthbuild.build(B / 'sdk', stage / 'assets/forth-src', stage / 'assets/forth-bin')
    sdkpack.pack(S / 'zx-ux-sdk', S / 'zx-ux', B, stage / 'sdk/bin')
    fortranpack.package(S, stage, B / 'sdk')
    shutil.copy2(R / 'LICENSE', stage / 'LICENSE')
    shutil.copy2(R / 'THIRD-PARTY', stage / 'THIRD-PARTY')
    shutil.copytree(S / 'zx-ux', stage / 'zx-ux/src', ignore=no_cache)
    # Final payload step: include documentation only after all builders succeed.
    # Stage it before publication so failed copies cannot damage last-good dist/.
    shutil.copytree(docs, stage / 'docs', ignore=no_cache)
    # Publication happens only after every builder has succeeded.
    had_previous = D.exists()
    if had_previous:
        D.rename(B / 'dist-old')
    try:
        stage.rename(D)
    except BaseException:
        if had_previous and not D.exists():
            (B / 'dist-old').rename(D)
        raise
    if had_previous:
        shutil.rmtree(B / 'dist-old')


if __name__ == '__main__':
    main()
