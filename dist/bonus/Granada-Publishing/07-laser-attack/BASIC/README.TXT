LASER ATTACK — GRANADA PUBLISHING

We kept the original LaserAttack.tap from the Granada Publishing ZIP. The second original TAP copy matches it byte for byte. The data contains 4,685 BASIC program bytes and 262 saved bytes. The later TZX copy supplied in the ZIP has the same BASIC program bytes. LaserAttack.bas was regenerated with the ZX-UX ROM LLIST tool and has 186 numbered lines. The original tape stays the source for exact bytes.

The game starts with a difficulty choice from 1 to 10. The player pilots a laser ship across a blue field in pursuit of another craft. Press 7 to fire. The source turns the ship for any other key. The replay chooses difficulty 1, uses 8 to turn twice, and fires with 7 between the turns. It takes a fair bit of BASIC work just to draw the ship; the launch crew could have brought sandwiches.

REPLAY.sh uses the original TAP in genuine Fuse 48K at 100% speed. Four PNG views show the moving craft before and after real input. The game screen appears after a long source setup stage, so the script waits 18 seconds after the difficulty choice. We inspected actual gameplay, not just the title. No hit or full win is claimed, and bin/ remains empty for future native builds.

Original TAP SHA-256: a1f770183158fe3e0b937b37c0d44ca3fc76586983eb0af48c17a989163ab8ad
Original TAP bytes: 4972
Recreated TZX SHA-256: ca0d1e938ba8f0322eb848de71e90153cc8be76ed2dbebe00db9770ba8641fd5
Recreated TZX bytes: 4726
Regenerated BAS SHA-256: 014b2435ef49946e7ef2c32a6035a5e0c8eddbf3834c7ba5394c313078f872d5
Regenerated BAS bytes: 4709

From the repository root, run:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/07-laser-attack/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
