"""ZX-UX validation description.




"""
from __future__ import annotations

FLAGS2 = 23658
PIP = 23609
FRAMES = (23672, 23673, 23674)
PRIVATE = frozenset((FLAGS2, PIP, *FRAMES))
_MASK24 = (1 << 24) - 1


class ProcessSystemVariables:
    """One BASIC process's virtual ROM-compatible system-variable state."""

    def __init__(self, *, flags2=0, pip=0, frames=0):
        self._flags2 = flags2 & 255
        self._pip = pip & 255
        self._frames = frames & _MASK24
        self._last_tick = None

    @property
    def frames(self):
        return self._frames

    def peek(self, address):
        if address == FLAGS2:
            return self._flags2
        if address == PIP:
            return self._pip
        if address in FRAMES:
            return (self._frames >> (8 * (address - FRAMES[0]))) & 255
        raise ValueError(f'not a virtual Spectrum system variable: {address}')

    def poke(self, address, value):
        value = int(value) & 255
        if address == FLAGS2:
            self._flags2 = value
        elif address == PIP:
            self._pip = value
        elif address in FRAMES:
            shift = 8 * (address - FRAMES[0])
            self._frames = (self._frames & ~(255 << shift)) | (value << shift)
        else:
            raise ValueError(f'not a virtual Spectrum system variable: {address}')

    def tick(self, frames=1):
        if frames < 0:
            raise ValueError('frame count cannot go backwards')
        self._frames = (self._frames + frames) & _MASK24
        return self._frames

    def sync(self, kernel_tick):
        """ZX-UX validation description.



"""
        if not 0 <= kernel_tick <= 0xffff:
            raise ValueError('kernel tick must be unsigned 16-bit')
        if self._last_tick is not None:
            self.tick((kernel_tick - self._last_tick) & 0xffff)
        self._last_tick = kernel_tick
        return self._frames
