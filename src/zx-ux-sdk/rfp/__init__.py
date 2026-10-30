"""rfc - the ZX-UX Forth compiler (pure Python, MIT).

Forth source -> ras-syntax Z80 asm -> .sso (ras) -> .ssx (rld), mirroring the
rcc chain so a Forth program becomes an ordinary ZX-UX executable.

This is the Phase 0 proof-of-concept: a trivial subset that proves the whole
pipeline end to end. The full indirect-threaded compiler and a native,
syscall-based Forth runtime (porting the MIT M4_FORTH word set) come next.
"""
