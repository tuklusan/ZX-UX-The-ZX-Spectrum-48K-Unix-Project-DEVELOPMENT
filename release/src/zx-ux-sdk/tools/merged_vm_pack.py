"""Adapt the self-contained SDK VM to the single-CODE-block shipped TAP."""
from __future__ import annotations
import hashlib


def rewrite(source: str, syms: dict, image: bytes, low: bytes, kern: bytes, fs: bytes):
    original = "DEFAULT_SYSTEM = os.path.normpath(os.path.join(HERE, '..', 'build', 'ZX-UX.tap'))"
    replacement = "DEFAULT_SYSTEM = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'zx-ux', 'ZX-UX.tap'))"
    if source.count(original) != 1:
        raise RuntimeError('VM system-image locator changed unexpectedly')
    source = source.replace(original, replacement)
    low_addr, itab = syms['LOWK'], syms['ITAB']
    if (len(image) != itab + len(fs) - low_addr or
            image[:len(low)] != low or
            image[0x6000-low_addr:0x6000-low_addr+len(kern)] != kern or
            image[itab-low_addr:] != fs):
        raise RuntimeError('Merged VM sections differ from the linked binaries')
    info = {k: syms[k] for k in ('NPROC', 'SFREE', 'p_stat', 'p_pid', 'cur', 'scrown')}
    entries = [('lowk', low_addr, len(low)),
               ('unix', 0x6000, len(kern)),
               ('fs', itab, len(fs))]
    banner = ('EXPECTED_SYSTEM_SYMBOLS = ' + repr(info) + '\n' +
              'EXPECTED_SYSTEM_LOADS = ' + repr(entries) + '\n' +
              'EXPECTED_LOW_ADDR = ' + str(low_addr) + '\n' +
              'EXPECTED_IMAGE_LENGTH = ' + str(len(image)) + '\n' +
              'EXPECTED_GAP_START = ' + str(len(low)) + '\n' +
              'EXPECTED_GAP_END = ' + str(0x6000-low_addr) + '\n')
    start = source.index('class SystemImage:')
    end = source.index('# ---------------------------------------------------------------- keyboard', start)
    klass = '''class SystemImage:
    """Verified kernel sections decoded from the shipped merged boot tape."""

    def __init__(self, tape=None, kernel_json=None):
        if kernel_json is not None:
            raise RvmError('This SDK uses the self-contained shipped system image')
        self.tape = os.path.abspath(tape or DEFAULT_SYSTEM)
        if not os.path.isfile(self.tape):
            raise RvmError('No ZX-UX system tape: ' + self.tape)
        self.blocks = read_tape(self.tape)
        if len(self.blocks) != 4:
            raise RvmError('System tape must have one BASIC and one CODE pair')
        basic, basic_data, hdr, data = self.blocks
        if (len(basic) != 19 or basic[0] != 0 or basic[1] != 0 or
                basic_data[0] != 255 or
                len(hdr) != 19 or hdr[0] != 0 or hdr[1] != 3 or
                hdr[2:12].rstrip(b' ') != b'ZX-UX' or
                int.from_bytes(hdr[12:14], 'little') != EXPECTED_IMAGE_LENGTH or
                int.from_bytes(hdr[14:16], 'little') != EXPECTED_LOW_ADDR or
                len(data) != EXPECTED_IMAGE_LENGTH + 2 or data[0] != 255):
            raise RvmError('System tape has an incorrect merged load span')
        for block in self.blocks:
            if len(block) < 2:
                raise RvmError('System tape has a bad block')
            parity = 0
            for octet in block:
                parity ^= octet
            if parity:
                raise RvmError('System tape has a parity error')
        self.merged = bytes(data[1:-1])
        if any(self.merged[EXPECTED_GAP_START:EXPECTED_GAP_END]):
            raise RvmError('Merged image gap is not empty')
        if self.merged[0x6000 - EXPECTED_LOW_ADDR] != 0xc3:
            raise RvmError('Incorrect entry instruction in the system image')
        self.sym = EXPECTED_SYSTEM_SYMBOLS.copy()
        self.syscall = 0x6003
        self.info = {'format': 'zx-ux-kernel/1', 'symbols': self.sym, 'syscall': self.syscall}
        digest = hashlib.sha256()
        for block in self.blocks:
            digest.update(struct.pack('<H', len(block)) + block)
        self.sha256 = digest.hexdigest()

    def _code_block(self, name):
        for label, address, length in EXPECTED_SYSTEM_LOADS:
            if label == name:
                offset = address - EXPECTED_LOW_ADDR
                return self.merged[offset:offset + length]
        raise RvmError('Unknown system section: ' + name)


'''
    # The source file remains the canonical, generic SDK tool; this
    # generated module knows only the exact release image it accompanies.
    return source[:start] + banner + '\n' + klass + source[end:]
