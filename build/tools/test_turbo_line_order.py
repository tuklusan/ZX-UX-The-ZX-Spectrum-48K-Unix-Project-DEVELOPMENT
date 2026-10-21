#!/usr/bin/env python3
"""Exercise the assembled turbo display path with 24 successful packets.

The receiver and payload copy are stubbed only to avoid replaying the tape;
all progress-row rendering, counters, and final handover run as Z80 code.
Run after build/build.py, with the assembler executable as first argument.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'build/src'
SDK = ROOT / 'src/zx-ux-sdk'
sys.path.insert(0, str(SDK))
import zxcore  # noqa: E402


def check(sjasm: str) -> None:
    with tempfile.TemporaryDirectory() as scratch:
        binary = Path(scratch) / 'loader.bin'
        symbols = Path(scratch) / 'loader.sym'
        subprocess.run([sjasm, '--nologo', '--sym=' + str(symbols),
                        '--raw=' + str(binary), 'turbo_boot.asm'],
                       cwd=STAGE, check=True, capture_output=True, text=True)
        sym = {}
        for line in symbols.read_text().splitlines():
            match = re.match(r'(\S+): EQU 0x([0-9a-fA-F]+)', line)
            if match:
                sym[match[1]] = int(match[2], 16)
        code = binary.read_bytes()
        assert code == (ROOT / 'build/out/turbo_boot.bin').read_bytes(), 'wrong assembled loader'

    machine = zxcore.Spectrum()
    mem = machine.mem
    mem[0xD000:0xD000 + len(code)] = code
    receiver, copier = sym['receive_frame'], sym['copy_payload']
    # OR A / RET: a successful CRC-checked turbo block without EAR edges.
    # RET: emulate the transfer, leaving the real display path untouched.
    mem[receiver:receiver + 2] = b'\xB7\xC9'
    mem[copier] = 0xC9

    # These four bottom-right attribute cells belong to the BASIC ribbon.
    ribbon = 0x5800 + 23 * 32 + 28
    mem[ribbon:ribbon + 4] = bytes((0x12, 0x36, 0x14, 0x25))

    machine.set(pc=0xD000)
    assert machine.run((receiver,), machine.t + 20_000_000), 'no first turbo request'
    lines_base = sym['progress_lines']
    row_index, ordinal, cursor = (sym[n] for n in ('row_index', 'ordinal', 'text_cursor'))

    def word(a):
        return mem[a] | (mem[a + 1] << 8)

    # Before receiving any turbo packet, line 1 is already on screen.
    assert mem[row_index] == 1 and mem[ordinal] == 1
    assert word(cursor) == lines_base + 64

    bottom = [0x4000 + 0x1000 + 32 * 7 + (y * 256) for y in range(8)]

    def last_row_drawn():
        return any(any(mem[addr:addr + 28]) for addr in bottom)

    assert not last_row_drawn(), 'bottom line appeared too early'

    for packet in range(1, 25):
        assert mem[ordinal] == packet
        # Resume at the stubbed receiver RET with carry clear.
        machine.set(pc=receiver + 1, f=machine.flags & ~1)
        finish = (receiver,) if packet < 24 else (0x03B5,)
        assert machine.run(finish, machine.t + 30_000_000), 'loader lost packet %d' % packet
        expected_rows = min(packet + 1, 24)
        assert mem[row_index] == expected_rows, (packet, mem[row_index])
        assert word(cursor) == lines_base + (64 * min(expected_rows, 23)) + (56 if expected_rows == 24 else 0), packet
        assert mem[ordinal] == packet + 1
        assert last_row_drawn() == (packet >= 23), 'last-line timing at packet %d' % packet
        assert bytes(mem[ribbon:ribbon + 4]) == b'\x12\x36\x14\x25', 'BASIC ribbon overwritten'

    print('PASS: 1 line before turbo block 1; lines 2-24 after blocks 1-23;')
    print('      line 24 remains visible during block 24; ROM beep reached, ribbon intact')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_turbo_line_order.py SJASMPLUS_PATH (after build)')
    check(sys.argv[1])
