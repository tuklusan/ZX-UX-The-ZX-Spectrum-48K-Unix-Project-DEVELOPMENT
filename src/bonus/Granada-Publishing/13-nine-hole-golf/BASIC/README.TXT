NINE HOLE GOLF — GRANADA PUBLISHING

We kept the original NineHoleGolf.tap from the Granada Publishing ZIP unchanged. Its supplied recreated TZX contains the same 4,380 tokenized BASIC program bytes. The regenerated Spectrum ROM listing has 157 numbered lines. The program draws a golfer, a flag, and bunkers on a course with random positions. The player enters a club number from 1 to 8 to take each stroke. The program can also switch to a putting screen.

We loaded the original TAP in Fuse SDL 1.6.0 on a 48K machine. We entered club 1, saw the on-screen report that the shot overshot the hole, then entered club 8. The second capture shows the next course view and another club prompt. Both screenshots are genuine Fuse views. Random course layouts may change between runs; neither a finished hole nor a complete nine-hole round was shown. Golf remains unkind to anyone using the biggest club for everything.

NineHoleGolf.bas was regenerated from the supplied recreated TZX using the ZX-UX ROM listing tool in a supplied repository copy. The tokenized program bytes match the original TAP. We did not use the original archive's separate .bas as independent tape proof or rewrite original media. No native executable is included; bin/ stays empty.

Original TAP SHA-256: 37dea98910616e842869f6591cd8ca67badcfd44d65c2b33e9f4e7335f3fdcef
Original TAP bytes: 4626
Supplied recreated TZX SHA-256: ffd33474b528c328d63e13772186de85f3e90d2688329a191569a0e4eadcf329
Supplied recreated TZX bytes: 4421
Regenerated BAS SHA-256: 2af2dc12837915e1a07e30d004e8ca99a78017f02b95f89777dbd6ad0d5618cf
Regenerated BAS lines: 157

From the repository root, run:
  sh src/bonus/Granada-Publishing/13-nine-hole-golf/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the original ZX-UX 48K ROM are needed.
