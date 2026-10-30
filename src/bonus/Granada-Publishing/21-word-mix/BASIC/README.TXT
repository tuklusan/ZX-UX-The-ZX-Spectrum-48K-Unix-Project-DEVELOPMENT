WORD MIX — GRANADA PUBLISHING

We kept the original WordMix.tap from the Granada Publishing archive. Its 2,108 BASIC program bytes match the supplied recreated TZX. We regenerated 70 numbered lines using the ZX-UX ROM LLIST converter.

The program mixes letters from two words and asks the player to name both words. We pressed Space to begin a round, then entered QUIT for the first answer and DOG for the second. The game showed the correct pair and a score of zero. In our live Fuse 48K run, the revealed words were GUITAR and RADIO. This is one sample round, not a full game. The pair may change on another run.

REPLAY.sh repeats the same inputs on the original TAP. Screenshots came from Fuse, not from the archive. No native binary is included.

Original TAP SHA-256: 0e6a5c64f28b08332e27a542e663dad3fe4c60003d24ac7fc899afe6e7712317
Recreated TZX SHA-256: d68c1e624123eaef2791e85f98ef4a3444ba3854f450b77edbf1ee42c1c17e74
Regenerated BASIC SHA-256: 6c104cbd014917287c0067fcad8b8b4d945710e12b77f0e86baee5e30b2f17f0

From the repository root:
  sh src/bonus/Granada-Publishing/21-word-mix/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
