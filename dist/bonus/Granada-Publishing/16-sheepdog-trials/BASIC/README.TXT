SHEEPDOG TRIALS — GRANADA PUBLISHING

We preserved the original SheepdogTrials.tap. Its first 2,820 tokenized BASIC program bytes match the supplied recreated TZX, while the TAP also contains stored variables. We regenerated 96 numbered BASIC lines using the ZX-UX ROM LLIST converter.

The dog moves around a fenced field, trying to drive the sheep toward a gate. The source reads 5 left, 8 right, 6 down, and 7 up. In genuine Fuse 48K, we pressed 8 and then 6. The on-screen move counter rose from 1 to 2; the game field changed as well. Both captures show the running field. No sheep was claimed as saved, and no complete game was played.

REPLAY.sh repeats the two presses on the original TAP. Images came from Fuse, not from the archive. No native binary is included.

Original TAP SHA-256: 4f7f5e7d51a18d50a46bc3e79a5992c05371c62ddaf20659c9f637d3ff12d45b
Recreated TZX SHA-256: 4ffeba6f5345da27ca658ff6087c67ccd70f419185ed5b097fb6b7aea0155684
Regenerated BASIC SHA-256: ff4b62a2d0a59507f28be4061b43b1fdd1693aba434d8cb390e7a9c6e5c57b34

From the repository root:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/16-sheepdog-trials/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
