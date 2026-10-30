MASTERBRAIN (MASTERMIND) — GRANADA PUBLISHING

We kept the original Mastermind.TAP from the Granada Publishing ZIP unchanged. The source archive also includes a recreated TZX; its 2,090 BASIC program bytes match the original TAP. The recovered ROM listing has 86 numbered lines. The player chooses four color digits from 3 through 6 to guess a four-color secret. The program marks exact matches and correct colors in other positions.

We ran the original TAP in Fuse SDL 1.6.0 on the 48K ROM, pressed Space at the tape stop prompt, entered age 20, then made guesses 3333 and 4444. Both attempts appeared on the board, and the guess number advanced. The two screenshots came from this real Fuse run and are not a complete match or a native build. The original tape sometimes leaves its stop notice visible among the colors. We have kept that screen as displayed rather than retouching it.

Mastermind.bas was generated from the supplied recreated TZX using the ZX-UX ROM listing tool from the supplied repository copy. We independently matched its tokenized program to the original TAP. No game bytes were changed. The bin/ folder has no native file.

Original TAP SHA-256: d30bfc93fdcb56999670ef900ba2692702690d13f41f06849b9c47a0f04cfac6
Original TAP bytes: 2308
Supplied recreated TZX SHA-256: 2dc9d06206ee4b52b95e68932ad7943f699541797bc52daa4e4692c5c7bcfb4f
Supplied recreated TZX bytes: 2131
Regenerated BAS SHA-256: 7087255f6569c1fb7627845cdc55f971cf04f21c2a2f4763223d3a0d1c073c5f
Regenerated BAS lines: 86

From the repository root, run:
  sh src/bonus/Granada-Publishing/10-mastermind/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the original ZX-UX 48K ROM are needed.
