MIRROR TILE — GRANADA PUBLISHING

We kept the original MirrorTile.tap from the Granada Publishing ZIP unchanged. Its supplied recreated TZX contains the same 5,087 tokenized BASIC program bytes. The ROM listing has 200 numbered lines. The program shuffles a four-by-four letter board. A player moves a tile next to the empty cell by entering its numbered position, from 1 through 16.

We played the original TAP using Fuse SDL 1.6.0 with the Spectrum 48K ROM. We declined custom words, chose two shuffles, then entered positions 12 and 16. The game showed a different board after each move and announced success in two moves. Both screenshots are from the real Fuse run. The original source needed no changes to win; that is a pleasant change of pace.

MirrorTile.bas was regenerated from the supplied recreated TZX using the ZX-UX ROM listing tool in the supplied repository copy. We compared its tokenized program with the original TAP. No native executable is included; the bin/ folder stays empty.

Original TAP SHA-256: 1bb60311cbbebee81064e863b5ab82724783bff1f61181102de0132fffae74f3
Original TAP bytes: 5467
Supplied recreated TZX SHA-256: 4b103189821c11920c5f3e7d79f98aa3706715def703f7315fd7e40835ac076d
Supplied recreated TZX bytes: 5128
Regenerated BAS SHA-256: e4cd7424fb600d2faa655dd147aa073486a21452ed7eef9452c8bfb926d6eecd
Regenerated BAS lines: 200

From the repository root, run:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/11-mirror-tile/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the original ZX-UX 48K ROM are needed.
