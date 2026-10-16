"""Offline boot-only turbo transport compiler, staged under retained tmp/.

Produces a compact timing/data TZX; independent verification gates must pass
before the staged distribution can replace last-good release/dist.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import shutil
import subprocess
import struct
import sys

from turbo_segments import layout, pack_tzx, read_segments, make_segments, COUNT, LOAD_BASE, ENTRY, MAX_TZX_BYTES, TurboFormatError
import osbuild

HERE = Path(__file__).resolve().parent
TMP = HERE / 'tmp'
SRC = TMP / 'src'
OUT = TMP / 'build'
ORIGINAL = HERE.parent / 'src/zx-ux/turbo_boot.asm'


def progress_lines(size: int, syms: dict, kernel: int, free: int):
    addr = syms['LOWK']
    end = addr + size - 1
    lines = [
        'ZX-UX UNIX v1 / 48K SPECTRUM',
        'Z80 CPU / 3.5 MHZ / 4 SLOTS',
        '1982 PLATFORM / 2026 ZX-UX',
        'SANYALNET LABS / BOOT SYSTEM',
        'BOOTING VIA TURBO CASSETTE',
        f'KERNEL {kernel} BYTES / 8192 MAX',
        f'SYSTEM IMAGE {size} BYTES',
        f'LOAD {addr:04X} THROUGH {end:04X}',
        f'ENTRY {ENTRY:04X} / LOWK PRESENT',
        'READ 24 VERIFIED IMAGE PARTS',
        'SEGMENT ENVELOPE V1 / ZX',
        'CRC16 + XOR ERROR CHECKING',
        'TAPE ADDRESSES ARE IGNORED',
        'PROTECTING BOOT-LOADER RAM',
        'ROM 48K / 24 PROGRESS ROWS',
        'USER PROGRAMS: STANDARD TAPE',
        'NO USERLAND TURBO REQUIRED',
        f'ARENA BOOT FREE {free} BYTES',
        '4 SLOTS / IX INTERFACE V1',
        'SSX1 PROGRAM / ENV1 SUPPORT',
        'TAR ARCHIVE / CASSETTE READY',
        'REWIND SAME BLOCK ON ERROR',
        'ROM BEEP AND BOOT HANDOVER',
        'ZX-UX UNIX / LOGIN NEXT',
    ]
    if len(lines) != COUNT or any(len(line) > 32 or not line.isascii() or not line.isprintable() for line in lines):
        raise TurboFormatError('bad turbo status line facts or width')
    return tuple(line.ljust(32) for line in lines)


def encode_basic():
    def val(n):
        return b'\xb0"' + str(n).encode() + b'"'
    # Loader at D000 is above cleared RAMTOP CEFF, and the merged image ends
    # below C200. The BASIC active stack is between C200 and CEFF.
    line = (b'\xfd' + val(0xCEFF) + b':' + b'\xef""\xaf:' +
            b'\xf9\xc0' + val(0xD000) + b'\r')
    return struct.pack('>H', 10) + struct.pack('<H', len(line)) + line


def create_tzx(sjasm: str, syms: dict, kernel: int, free: int, *, pause_ms=400, output_name="ZX-UX-turbo-experimental.tzx"):
    raw = (OUT/'merged-image.bin').read_bytes()
    if syms['LOWK'] != LOAD_BASE or len(raw) + LOAD_BASE > 0xCE00:
        raise TurboFormatError('merged image or protected loader stack address changed')
    plan = layout(len(raw), load_base=syms['LOWK'])
    lines = progress_lines(len(raw), syms, kernel, free)
    (SRC/'turbo_plan.inc').write_text(
        f'MAX_SEG_LEN equ {max(n for _,n in plan)}\n' +
        ''.join(f'        dw {off},{length}\n' for off, length in plan))
    (SRC/'turbo_lines.inc').write_text(
        ''.join(f'        db "{line}"\n' for line in lines))
    shutil.copyfile(ORIGINAL, SRC/'turbo_boot.asm')
    loader = OUT/'turbo_boot.bin'
    result = subprocess.run([sjasm, '--nologo', f'--raw={loader}', 'turbo_boot.asm'],
                            cwd=SRC, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Turbo loader assembly failed:\n'+result.stdout+result.stderr)
    code = loader.read_bytes()
    if not 100 < len(code) < 0x1000:
        raise TurboFormatError('bootstrap outside inspected D000-DFFF range')
    standard = (osbuild.header(0,'ZX-UX UNIX',len(encode_basic()),10,len(encode_basic())),
                osbuild.tap_block(0xFF,encode_basic()))
    bootstrap = (osbuild.header(3,'ZX-UX BOOT',len(code),0xD000,0x8000),
                 osbuild.tap_block(0xFF,code))
    tzx = pack_tzx(standard, bootstrap, raw, pause_ms=pause_ms)
    if output_name not in ('ZX-UX-turbo-experimental.tzx', 'ZX-UX.tzx'):
        raise TurboFormatError('invalid boot output name')
    target = OUT/output_name
    if len(tzx) >= MAX_TZX_BYTES:
        raise TurboFormatError('boot TZX is at least 30,000 bytes')
    target.write_bytes(tzx)
    from turbo_verify import check_tzx
    check_tzx(target, raw, code, load_base=syms['LOWK'])
    if read_segments(make_segments(raw), image_length=len(raw)) != raw:
        raise TurboFormatError('generated tape image failed independent reconstruction')
    return target, len(code), lines


def main():
    import re
    if len(sys.argv) != 2:
        raise SystemExit('usage: turbo_boot_build.py SJASMPLUS-1.24.0')
    syms = {}
    for line in (SRC/'unix.sym').read_text().splitlines():
        m = re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)', line)
        if m:
            syms[m.group(1)] = int(m.group(2), 16)
    image = (OUT/'merged-image.bin').read_bytes()
    _, _, free, _ = osbuild.mkfs(syms, osbuild.program_list())
    tape, size, lines = create_tzx(sys.argv[1],syms, syms['kend']-0x6000,free)
    print('EXPERIMENTAL boot turbo:', tape, '| ROM bootstrap', size, 'bytes; image',len(image),'bytes')

if __name__ == '__main__':
    main()
