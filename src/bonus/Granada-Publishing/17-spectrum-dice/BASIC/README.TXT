SPECTRUM DICE — GRANADA PUBLISHING

We kept the original SpectrumDice.tap from the Granada Publishing archive. Its 1,161 tokenized BASIC program bytes match those in the supplied recreated TZX. We regenerated 55 numbered BASIC lines with the ZX-UX ROM LLIST converter.

The program draws a large die and asks the player to press any key to throw. We pressed Return to pass the first prompt, then Space three times during a real Fuse 48K session. The saved pictures after the first and third throws show different pip patterns. The second throw produced the same visible pattern as the first. The BASIC source uses RND to choose each face; a repeated face is quite possible. We did not change its random choices.

REPLAY.sh loads the original tape and sends those keys. The screenshots come from genuine Fuse play. No native binary is included.

Original TAP SHA-256: acbe7d24e64a7e3bd2964e5787832e0d61ec2deb2ccdce8cdd45cd9f07961b17
Recreated TZX SHA-256: 2ddae9438dee5cd3cec1076604001b2d20947fc8738e8a7fb45e7b9fcc07237a
Regenerated BASIC SHA-256: 8cf01f7afe9afcc2bb2be4dd32c4b8c95165eba4e446fccdcba2e7f38c7ea98a

From the repository root:
  sh src/bonus/Granada-Publishing/17-spectrum-dice/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
