#!/usr/bin/env python3
"""Build ZX-UX in place without replacing release/dist or its other contents."""
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
R = pathlib.Path(__file__).resolve().parents[1]
B, S, D = R / 'build', R / 'src', R / 'dist'
sys.path.insert(0, str(S / 'zx-ux-sdk/tools'))
import osbuild, turbo_boot_build, c48build, sdkpack

MANIFEST = '.zxux-generated.json'
GENERATED = ('assets/c48-bin', 'sdk/bin', 'zx-ux/ZX-UX.tzx')


def regular(path):
    mode = path.lstat().st_mode
    return stat.S_ISREG(mode)


def directory(path):
    mode = path.lstat().st_mode
    return stat.S_ISDIR(mode)


def safe_tree(root, required=True):
    """Reject links and special files, including a linked root."""
    if not root.exists() and not root.is_symlink() and not required:
        return False
    if not directory(root):
        raise RuntimeError('Unsafe directory: ' + str(root))
    for path in root.rglob('*'):
        if not (regular(path) or directory(path)):
            raise RuntimeError('Unsafe path: ' + str(path))
    return True


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def owned_by_checkout(path):
    """Only bootstrap tracked, unmodified generated output files."""
    relative = path.relative_to(R.parent).as_posix()
    found = subprocess.run(['git', '-C', str(R.parent), 'ls-files', '--error-unmatch',
                            '--', relative], capture_output=True)
    if found.returncode:
        return False
    saved = subprocess.run(['git', '-C', str(R.parent), 'show',
                            'HEAD:' + relative], capture_output=True)
    if saved.returncode:
        return False
    current = path.read_bytes()
    # A ZIP checkout may have Windows CRLF where the Git blob uses LF.
    # Accept this one exact transform, never arbitrary edited content.
    return current == saved.stdout or current.replace(b'\r\n', b'\n') == saved.stdout


def staged_files(stage):
    files = {}
    for relative in GENERATED:
        root = stage / relative
        if not root.exists():
            raise RuntimeError('Missing generated output: ' + str(root))
        if root.is_dir():
            safe_tree(root)
            for p in root.rglob('*'):
                if regular(p):
                    files[p.relative_to(stage).as_posix()] = p
        elif regular(root):
            files[relative] = root
        else:
            raise RuntimeError('Unsafe generated output: ' + str(root))
    return files


def install(stage):
    """Validate ownership first; replace individual files and roll back on error."""
    safe_tree(D)
    files = staged_files(stage)
    manifest = D / MANIFEST
    if manifest.is_symlink():
        raise RuntimeError('Linked build manifest')
    previous = {}
    if manifest.exists():
        if not regular(manifest):
            raise RuntimeError('Invalid build manifest')
        stored = json.loads(manifest.read_text(encoding='utf-8'))
        if stored.get('version') != 1 or not isinstance(stored.get('files'), dict):
            raise RuntimeError('Unknown build manifest')
        previous = stored['files']
    desired = {}
    changed = []
    for relative, source in sorted(files.items()):
        dest = D / relative
        # D itself was checked above. Do not create or cross linked directories.
        for parent in list(dest.parents):
            if parent == D:
                break
            if parent.is_symlink() or (parent.exists() and not directory(parent)):
                raise RuntimeError('Unsafe destination parent: ' + str(parent))
        digest = sha256(source)
        desired[relative] = digest
        if dest.is_symlink():
            raise RuntimeError('Linked generated destination: ' + str(dest))
        if dest.exists():
            if not regular(dest):
                raise RuntimeError('Unsafe generated destination: ' + str(dest))
            current = sha256(dest)
            if current == digest:
                continue
            if relative in previous:
                if current != previous[relative]:
                    raise RuntimeError('User-modified generated file: ' + relative)
            elif not owned_by_checkout(dest):
                raise RuntimeError('Unowned output collision: ' + relative)
        changed.append((source, dest))
    new_manifest = (json.dumps({'version': 1, 'files': desired},
                               indent=2, sort_keys=True) + '\n').encode('utf-8')
    if manifest.exists() and manifest.read_bytes() == new_manifest and not changed:
        return
    # Each backup and temporary file lives on the destination filesystem.
    # A complete set of backups is prepared before changing any destination.
    undo = []
    temporary = []
    try:
        for source, dest in changed:
            dest.parent.mkdir(parents=True, exist_ok=True)
            handle, tmp = tempfile.mkstemp(prefix='.zxux-new-', dir=dest.parent)
            os.close(handle)
            tmp = pathlib.Path(tmp)
            temporary.append(tmp)
            shutil.copy2(source, tmp)
            backup = None
            if dest.exists():
                handle, name = tempfile.mkstemp(prefix='.zxux-old-', dir=dest.parent)
                os.close(handle)
                backup = pathlib.Path(name)
                temporary.append(backup)
                shutil.copy2(dest, backup)
            undo.append((dest, backup))
            # Store each prepared new file so no reading from the staging tree
            # is required once publication starts.
            undo[-1] += (tmp,)
        handle, name = tempfile.mkstemp(prefix='.zxux-new-', dir=D)
        os.close(handle)
        manifest_new = pathlib.Path(name)
        temporary.append(manifest_new)
        manifest_new.write_bytes(new_manifest)
        manifest_old = None
        if manifest.exists():
            handle, name = tempfile.mkstemp(prefix='.zxux-old-', dir=D)
            os.close(handle)
            manifest_old = pathlib.Path(name)
            temporary.append(manifest_old)
            shutil.copy2(manifest, manifest_old)
        replaced = []
        try:
            for dest, backup, tmp in undo:
                os.replace(tmp, dest)
                replaced.append((dest, backup))
            os.replace(manifest_new, manifest)
        except BaseException:
            for dest, backup in reversed(replaced):
                if backup is None:
                    dest.unlink()
                else:
                    os.replace(backup, dest)
            if manifest_old is not None:
                os.replace(manifest_old, manifest)
            elif manifest.exists() and manifest_new not in temporary:
                manifest.unlink()
            raise
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def main():
    argv = sys.argv[1:]
    argv = argv[1:] if argv[:1] == ['--sjasm'] else argv
    sjasm = (str(pathlib.Path(argv[0]).resolve()) if len(argv) == 1
             else shutil.which('sjasmplus') or 'sjasmplus')
    safe_tree(D)
    safe_tree(D / 'assets/c48-src')
    safe_tree(D / 'bonus', required=False)
    safe_tree(B)
    for name in ('src', 'sdk', 'out', 'dist-stage'):
        path = B / name
        if path.is_symlink() or (path.exists() and not directory(path)):
            raise RuntimeError('Unsafe build workspace: ' + str(path))
        if path.exists():
            shutil.rmtree(path)
    stage = B / 'dist-stage'
    shutil.copytree(D / 'assets/c48-src', stage / 'assets/c48-src')
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
    install(stage)


if __name__ == '__main__':
    main()
