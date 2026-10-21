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
TMP = HERE.parents[2] / 'build'
SRC = TMP / 'src'
OUT = TMP / 'out'
ORIGINAL = HERE.parent.parent / 'zx-ux/turbo_boot.asm'


def progress_lines(size: int, syms: dict, kernel: int, free: int):
    """24 canonical 32-character messages, in the supplied v02 file order.

    The beta default time is 09:00:00, unlike the older reference's 00:00:00.
    The 4x8 renderer places each glyph in a 64-column cell followed by a
    blank half-character for clear legibility, retaining the exact wording.
    """
    source = (HERE.parent.parent / 'zx-ux/turbo_lines.txt').read_text().splitlines()
    if len(source) != COUNT or any(not s.isascii() or not s.isprintable() or len(s) > 32 for s in source):
        raise TurboFormatError('invalid 24-line canonical loader message file')
    return tuple(s.ljust(32) for s in source)


def encode_basic():
    def val(n):
        return b'\xb0"' + str(n).encode() + b'"'
    # Keep the four bottom-right attribute cells set during boot. The
    # 64-column progress renderer leaves these four 32-column cells alone.
    line = (b'\xe7' + val(0) + b':' + b'\xda' + val(0) + b':' +
            b'\xd9' + val(7) + b':' + b'\xfd' + val(0xCEFF) + b':' +
            b'\xef""\xaf:' + b'\xfb:' +
            osbuild.ribbon_print(val) + b':' +
            b'\xf9\xc0' + val(0xD000) + b'\r')
    return struct.pack('>H', 10) + struct.pack('<H', len(line)) + line


def expanded_line(line: str):
    return ''.join(c+' ' for c in line)


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
        ''.join(f'        db "{expanded_line(line)}"\n' for line in lines))
    shutil.copyfile(ORIGINAL, SRC/'turbo_boot.asm')
    shutil.copyfile(HERE.parent.parent / 'zx-ux/font4x8.bin', SRC/'font4x8.bin')
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
