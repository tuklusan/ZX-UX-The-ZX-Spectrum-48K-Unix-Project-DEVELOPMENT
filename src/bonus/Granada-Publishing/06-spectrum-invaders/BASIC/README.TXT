SPECTRUM INVADERS — GRANADA PUBLISHING

We kept the original SpectrumInvaders.tap from the Granada Publishing ZIP. The matching TAP in original-medium/ has identical bytes. The data block holds 3,729 bytes of BASIC program and 150 bytes of saved values. We also kept the later recreated TZX from the ZIP. Its BASIC program bytes match the original TAP exactly.

SpectrumInvaders.bas was regenerated with the ZX-UX ROM LLIST tool and contains 137 numbered lines. The tape remains the source for the real character and program bytes. The BASIC sets up rows of aliens, a green launcher near the bottom, and missiles. Press 5 to steer left, 8 to steer right, and 7 to fire. The source checks these three keys during the game loop. A missile may be faster than the paperwork, which is the proper order of things.

The replay opens the original TAP in Fuse SDL 1.6.0 at 50% speed. It sends left, right, and fire, then saves three live screen images. We inspected the changing launcher position and the firing view. This shows a short game session, not a cleared screen or a native build. No compiled file is included; bin/ remains empty.

Original TAP SHA-256: 9f1610e441d932106c53d844b82c6c8ac962fa939472058be11fca5d90ff5f48
Original TAP bytes: 3904
Recreated TZX SHA-256: f73c0bfaeda825a85a89be902c134335407d794f3c5d6e3a17f4c3394ddfa4c6
Recreated TZX bytes: 3770
Regenerated BAS SHA-256: 633a88acbfad107779a5f696c055ec00839fcd40b95e6473d482ee37b8acfdab
Regenerated BAS bytes: 3844

From the repository root, run:
  sh src/bonus/Granada-Publishing/06-spectrum-invaders/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
