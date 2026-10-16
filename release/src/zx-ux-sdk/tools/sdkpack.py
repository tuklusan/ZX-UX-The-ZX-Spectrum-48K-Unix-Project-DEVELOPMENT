"""Prepare the independent-host ZX-UX SDK in its final bin/ directory."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import struct

EXCLUDE = {'__pycache__', 'tests', 'tools'}
EXTRA_EXCLUDE = {'README.md', 'THIRD-PARTY.md'}

def pack(sdk_source: Path, os_source: Path, os_build: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    support = output / 'py'
    support.mkdir(exist_ok=True)
    for path in sorted(sdk_source.rglob('*')):
        if path.is_dir() or EXCLUDE.intersection(path.relative_to(sdk_source).parts):
            continue
        rel = path.relative_to(sdk_source)
        if rel.name in EXTRA_EXCLUDE or rel.parts[0] == 'bin' or rel in (Path('LICENSE'), Path('THIRD-PARTY.txt')):
            continue
        target = support / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    rom = support / 'rom'
    rom.mkdir(exist_ok=True)
    shutil.copyfile(os_source / 'rom/48.rom', rom / '48.rom')
    shutil.copyfile(os_source / 'font4x8.bin', rom / 'font4x8.bin')
    # Required notices accompany the independent SDK.
    shutil.copyfile(sdk_source / 'LICENSE', output / 'LICENSE')
    shutil.copyfile(sdk_source / 'THIRD-PARTY.txt', output / 'THIRD-PARTY.txt')
    # All command shims are directly in sdk/bin/, alongside their modules.
    for script in sorted((sdk_source / 'bin').iterdir()):
        if not script.is_file():
            continue
        body = script.read_text()
        needle = "os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')"
        body = body.replace('os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")', needle)
        if needle not in body:
            raise RuntimeError('Unrecognized SDK command shim: ' + script.name)
        body = body.replace(needle, "os.path.join(os.path.dirname(os.path.abspath(__file__)), 'py')")
        target = output / script.name
        target.write_text(body)
        target.chmod(0o755)
    # The packaged SDK has no duplicate image, no file outside dist/sdk/bin,
    # and carries a self-checking decoder of the exact merged TAP.
    from merged_vm_pack import rewrite
    syms = {}
    for line in (os_build / 'src/unix.sym').read_text().splitlines():
        parts = line.split(': EQU 0x')
        if len(parts) == 2:
            syms[parts[0]] = int(parts[1], 16)
    out = os_build / 'out'
    image = (out / 'merged-image.bin').read_bytes()
    source = (support / 'zxux.py').read_text()
    (support / 'zxux.py').write_text(rewrite(
        source, syms, image,
        (out / 'lowk.bin').read_bytes(),
        (out / 'unix.bin').read_bytes(),
        (out / 'fs.img').read_bytes()))
    return 3
