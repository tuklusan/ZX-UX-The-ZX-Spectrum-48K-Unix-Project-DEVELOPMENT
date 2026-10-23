"""Adapt HiSoft's existing PAUSE runtime to ZX-UX's interrupt environment.

The Spectrum ROM PAUSE loop expects ROM keyboard scans to set FLAGS bit 5.
ZX-UX runs its own interrupt handler, so request the ROM keyboard scan once
per paused frame. Keep HiSoft's existing call sites, data, and expression code.
"""
from __future__ import annotations

def install(compiler):
    """Override only HiSoft RT.PAUSE emission; other emitters remain upstream."""
    from z80asm import asm
    from rtnames import RT
    runtime = compiler.rtlib
    base = runtime.Machine
    if getattr(base, '_zxux_native_pause', False):
        return

    # The ROM keyboard routine at 02BF updates the original key status and FLAGS.
    # A zero BC means wait indefinitely; a nonzero BC counts interrupts.
    # Relative branch offsets refer to this fixed 45-byte routine.
    pause_native = asm(
        'ld b,h; ld c,l; ld a,($5c3b); and $df; ld ($5c3b),a;'
        'halt; push bc; call $02bf; pop bc; ld a,($5c3b); and $20;'
        'jr nz,+13; dec bc; ld a,b; or c; jr z,+8;'
        'ld a,b; and c; inc a; jr nz,-23; inc bc; jr -26;'
        'ld a,($5c3b); and $df; ld ($5c3b),a; ret'
    )
    assert len(pause_native) == 45


    class ZXUXPauseMachine(base):
        _zxux_native_pause = True

        def run_emitter(self, n, pc, counting, code_base):
            if n != RT.PAUSE:
                return super().run_emitter(n, pc, counting, code_base)
            if not counting and not self.de_flags & 1:
                self.far[pc:pc + len(pause_native)] = pause_native
            return pc + len(pause_native)

    runtime.Machine = ZXUXPauseMachine
