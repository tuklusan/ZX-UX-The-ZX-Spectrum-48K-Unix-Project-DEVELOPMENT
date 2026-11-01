FRUIT MACHINE — GRANADA PUBLISHING

We kept the original FruitMachine.tap from the Granada Publishing ZIP without changing its bytes. The second TAP copy in the ZIP matches it. The tape has one BASIC header and one data block. Its program holds 2,351 bytes of BASIC, followed by 57 bytes of saved values.

FruitMachine-recreated-tape.TZX is the later tape copy supplied in the ZIP's BASIC folder. Its BASIC program bytes match the original TAP. FruitMachine.bas was regenerated from that TZX with the ZX-UX ROM LLIST tool. The listing has 85 numbered lines. The original TAP remains the source for exact machine bytes.

The game begins with 100p, charges 10p for each spin, and shows three fruit symbols. The source gives different prizes for matching symbols. When the game asks for another spin, Y plays again; any other key ends the session. Luck has a long history of ignoring sensible plans.

REPLAY.sh loads the original tape in Fuse 48K at 50% speed. It waits for the first result, then presses Y twice, once after each completed spin. The three files in SCREENSHOTS record real Fuse game screens. In the checked run, the money read 95p, 90p, and 85p. Other runs can show different values. The images show short real play, not a complete run or native build. No compiled file is included; bin/ stays empty.

Original TAP SHA-256: 2aeb464249ffbde71e2afc5a26a892f6278e0ab316d62c4775cf2d9ab2225ff2
Original TAP bytes: 2433
Recreated TZX SHA-256: 6d8122804702a4ab2dbe7604f1266a907a1ac1141d50d8c2212f41a11b048a4e
Recreated TZX bytes: 2392
Regenerated BAS SHA-256: 78d1d94097caa61ed445dd99a8abdc67700390cea45221ff97677238b818539a
Regenerated BAS bytes: 2434

From the repository root, run:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/04-fruit-machine/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
