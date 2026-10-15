"""Prepare the independent-host ZX-UX SDK in its final bin/ directory."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import struct

EXCLUDE = {'__pycache__', 'tests'}
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
    # No separate metadata or duplicate kernel tape is installed with the VM.
    symbols = {}
    for line in (os_build / 'src/unix.sym').read_text().splitlines():
        parts = line.split(': EQU 0x')
        if len(parts) == 2:
            symbols[parts[0]] = int(parts[1], 16)
    used = ('NPROC', 'SFREE', 'p_stat', 'p_pid', 'cur', 'scrown')
    info = {s: symbols[s] for s in used}
    # The VM accepts only an image whose load ranges and tape order match the
    # freshly linked system; it never loads stale, external observation files.
    output_image = os_build / 'build'
    code_lengths = {'unix': len((output_image / 'unix.bin').read_bytes()),
                    'fs': len((output_image / 'fs.img').read_bytes()),
                    'lowk': len((output_image / 'lowk.bin').read_bytes())}
    entries = [('unix', 0x6000, code_lengths['unix']),
               ('fs', symbols['ITAB'], code_lengths['fs']),
               ('lowk', symbols['LOWK'], code_lengths['lowk'])]
    source = (support / 'zxux.py').read_text()
    original = "DEFAULT_SYSTEM = os.path.normpath(os.path.join(HERE, '..', 'build', 'ZX-UX.tap'))"
    replacement = "DEFAULT_SYSTEM = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'zx-ux', 'ZX-UX.tap'))"
    if source.count(original) != 1:
        raise RuntimeError('VM system-image locator changed unexpectedly')
    source = source.replace(original, replacement)
    start = source.find('    def __init__(self, tape=None, kernel_json=None):', source.index('class SystemImage:'))
    end = source.find('    def _code_block(self, name):', start)
    if start < 0 or end < 0:
        raise RuntimeError('VM image reader changed unexpectedly')
    initializer = '''    def __init__(self, tape=None, kernel_json=None):
        if kernel_json is not None:
            raise RvmError('This SDK uses source-derived system observation data')
        self.tape = os.path.abspath(tape or DEFAULT_SYSTEM)
        if not os.path.isfile(self.tape):
            raise RvmError('No ZX-UX system tape: ' + self.tape)
        self.blocks = read_tape(self.tape)
        if len(self.blocks) != 8:
            raise RvmError('System tape: incorrect standard boot block count')
        ordered = EXPECTED_SYSTEM_LOADS
        for i, (name, addr, length) in enumerate(ordered, 1):
            hdr, data = self.blocks[i * 2], self.blocks[i * 2 + 1]
            if len(hdr) != 19 or hdr[0] != 0 or hdr[1] != 3 or hdr[2:12].rstrip(b' ') != name.encode():
                raise RvmError('System tape: missing CODE header for ' + name)
            if len(data) != length + 2 or data[0] != 255 or (int.from_bytes(hdr[12:14], 'little') != length) or (int.from_bytes(hdr[14:16], 'little') != addr):
                raise RvmError('System tape: incorrect load span for ' + name)
        for block in self.blocks:
            parity = 0
            for byte in block:
                parity ^= byte
            if parity:
                raise RvmError('System tape: parity error')
        self.sym = EXPECTED_SYSTEM_SYMBOLS.copy()
        self.syscall = 0x6003
        self.info = {'format': 'zx-ux-kernel/1', 'symbols': self.sym, 'syscall': self.syscall}
        digest = hashlib.sha256()
        for block in self.blocks:
            digest.update(struct.pack('<H', len(block)) + block)
        self.sha256 = digest.hexdigest()

'''
    banner = 'EXPECTED_SYSTEM_SYMBOLS = ' + repr(info) + '\nEXPECTED_SYSTEM_LOADS = ' + repr(entries) + '\n'
    at = source.find('class SystemImage:')
    source = source[:at] + banner + '\n' + source[at:start] + initializer + source[end:]
    (support / 'zxux.py').write_text(source)
    return len(entries)
