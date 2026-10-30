SAVE THE WHALE — GRANADA PUBLISHING

We kept the original SaveTheWhale.tap from the Granada Publishing archive. The TZX copy contains the same 2,751 BASIC program bytes as the original TAP; the TAP also contains stored variables. We regenerated all 102 numbered BASIC lines using the ZX-UX ROM LLIST converter.

The game asks the player to save a whale from moving kayaks by drawing them into icebergs. We selected level 3, then pressed 5 and 8 in a real Fuse 48K session. The source identifies 5 as left and 8 as right for the whale; 7 and 6 move it up and down. We captured two live views. The moving kayaks can also change the screen, so the images alone do not measure the whale's exact displacement. No completed escape is claimed.

REPLAY.sh loads the original TAP and repeats these keys. The pictures were captured from Fuse, not copied from the archive. No native binary is included.

Original TAP SHA-256: 9812e742b2fa60b4ab956847b02b9c63f2e525fa009cfb8a6646d3f9b3f4a3f7
Recreated TZX SHA-256: 758c3c53a8385a823a727c78126a4c13475dfbf173dc6ce18c98acd3a106804b
Regenerated BASIC SHA-256: f6f140fdca283db09e7f210f213e0e0dcb9c312e07269daef230fb400a0840c5

From the repository root:
  sh src/bonus/Granada-Publishing/15-save-the-whale/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
