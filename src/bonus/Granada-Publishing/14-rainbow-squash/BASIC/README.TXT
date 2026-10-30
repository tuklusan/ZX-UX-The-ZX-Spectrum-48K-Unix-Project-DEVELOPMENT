RAINBOW SQUASH — GRANADA PUBLISHING

We kept the original RainbowSquash.tap from the Granada Publishing archive. The supplied recreated TZX carries the same 1,821 tokenized BASIC program bytes as the TAP. The original TAP also carries stored variables. We regenerated the 80 numbered BASIC lines from the TZX with the ZX-UX ROM LLIST tool.

This game has a moving ball and a paddle near the bottom of a colored court. The BASIC source reads 5 to move left and 8 to move right. After the tape begins, Return advances the ball prompt. We pressed both movement keys during a live Fuse 48K session. The two screenshots show different court states. Since the ball also moves on its own, those image changes alone do not prove a specific paddle displacement. No win or full game is claimed.

REPLAY.sh runs the original TAP in Fuse SDL 1.6.0 and captures the two live views. The captures come from the emulator, not the archive. No native binary is included.

Original TAP SHA-256: f0f2cef952ae11b3fd4449a6036fcb88396f1c5f939c115adc36772061cdc130
Recreated TZX SHA-256: 13d9a670657ce6c7b4a3eea6f83476be6a88096dd165f595c677d42f3c621480
Regenerated BASIC SHA-256: 1268b98070eb453aec24e9101606b51156b5912cc83b19f0cb665b28d2239d06

From the repository root:
  sh src/bonus/Granada-Publishing/14-rainbow-squash/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
