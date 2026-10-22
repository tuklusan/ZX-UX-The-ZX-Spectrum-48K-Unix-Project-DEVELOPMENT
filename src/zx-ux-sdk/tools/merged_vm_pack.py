"""Adapt the self-contained SDK VM to the verified compact shipped TZX."""
from __future__ import annotations
import hashlib


def rewrite(source: str, syms: dict, image: bytes, low: bytes, kern: bytes, fs: bytes, bootstrap: bytes):
    original = "DEFAULT_SYSTEM = os.path.normpath(os.path.join(HERE, '..', '..', 'build', 'out', 'ZX-UX.tzx'))"
    replacement = "DEFAULT_SYSTEM = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'zx-ux', 'tzx', 'ZX-UX.tzx'))"
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
              'EXPECTED_IMAGE_SHA256 = ' + repr(hashlib.sha256(image).hexdigest()) + '\n' +
              'EXPECTED_BOOT_SHA256 = ' + repr(hashlib.sha256(bootstrap).hexdigest()) + '\n' +
              'EXPECTED_GAP_START = ' + str(len(low)) + '\n' +
              'EXPECTED_GAP_END = ' + str(0x6000-low_addr) + '\n')
    marker = 'class SystemImage:'
    if source.count(marker)!=1:
        raise RuntimeError('unrecognised SDK TZX reader')
    return source.replace(marker, banner + '\n' + marker)
