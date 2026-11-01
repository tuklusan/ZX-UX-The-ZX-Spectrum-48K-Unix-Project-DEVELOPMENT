MORSE CODE — GRANADA PUBLISHING

We kept the original MorseCode.tap from the Granada Publishing ZIP unchanged. The supplied recreated TZX contains the same 2,844 tokenized BASIC program bytes. The regenerated Sinclair 48K ROM listing has 98 numbered lines. Morse Code is an interactive teaching program, not a game with a score or a winning round.

The menu offers message sending, random letters, and a word exercise. We tested the message option on the original TAP in Fuse SDL 1.6.0. After starting the program, we selected 1, set speed 100, and sent HI. Its screen first displayed H, then HI as transmission advanced. Both saved images are genuine Fuse screen views. The tape plays tones using BASIC BEEP commands, but our silent emulator run did not check audio output. No Morse decoding skill is claimed. The letter I had considerably less trouble getting through than some of our other games.

MorseCode.bas was regenerated from the supplied recreated TZX using the ZX-UX ROM listing tool in a supplied repository copy. The TZX program bytes were checked against the original TAP; these source tapes were not edited. The original archive also has a separate non-LLIST .bas, which we did not use as independent tape proof. No native executable is included; bin/ stays empty.

Original TAP SHA-256: 26a263f861ea0200c6a7d4f2c48d3f430ebb8245b882ca47eda1b62f4d37e1e6
Original TAP bytes: 3333
Supplied recreated TZX SHA-256: 4538584cb040c48ffcffee2e08d6ea8331092fc2d8953aa8b37a9cbd7b1f187a
Supplied recreated TZX bytes: 2885
Regenerated BAS SHA-256: d0df4cd8d06af43cfb2ff9c11e81edaac4e34c542fd314aecea401ccc5c63f8b
Regenerated BAS lines: 98

From the repository root, run:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/12-morse-code/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the original ZX-UX 48K ROM are needed.
