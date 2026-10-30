NOUGHTS AND CROSSES — GRANADA PUBLISHING

We kept the original NoughtsAndCrosses.tap without changes. The supplied recreated TZX contains the same 2,787 BASIC program bytes as the original TAP. The checked ROM listing has 113 numbered BASIC lines. The human enters a row and column, each from 1 to 3. The human marks X and the computer marks O on a three-by-three board.

We played the original TAP in Fuse SDL 1.6.0 on a Spectrum 48K with its original ROM. We entered 11 and 22, pressed Enter after each pair, and inspected the two captured game boards. The second view shows another X and O, so the board changed with input. These are genuine Fuse screenshots, not a native build or a full game.

The source archive includes a recreated TZX and an earlier printer-style BASIC text. NoughtsAndCrosses.bas here was generated from that TZX using the ZX-UX ROM listing tool held in the supplied repository copy. The TZX program data was independently compared with the TAP program bytes. No source media was rewritten to change play. The bin/ folder has no native output.

Original TAP SHA-256: 5736864fc59e7cea9683aabfa229ee6652a477ea53b02af05c8654028c80f982
Original TAP bytes: 2976
Supplied recreated TZX SHA-256: 03867951b4a75269e029373460d117b685a6ca90af45ab235bac2a27bc83732f
Supplied recreated TZX bytes: 2828
Regenerated BAS SHA-256: 4da7bce1a23c492b142ff9ce7d17a192934d013d74028e3b000014f8dbff74f1
Regenerated BAS lines: 113

From the repository root, run:
  sh src/bonus/Granada-Publishing/09-noughts-and-crosses/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
