SPECTRUM SMALLTALK — GRANADA PUBLISHING

We kept the original SpectrumSmalltalk.tap. The BASIC part has 7,203 program bytes matching the supplied recreated TZX, and we regenerated 229 numbered lines using the ZX-UX ROM LLIST converter.

This is a simple text conversation program, not an action game. It asks the player to type a sentence and press Enter. We typed "i like games", then "my dog" during a genuine Fuse 48K session. The program replied to the first sentence with "In what way ?" and to the second with "your dog ?". Both replies are visible in the original emulator captures. The program chooses replies from its stored patterns; we make no claim that it understands free text.

REPLAY.sh repeats these two sentences on the original TAP. The screenshots came from Fuse, not from the archive. No native binary is included.

Original TAP SHA-256: bf8b91c87fc8db2ddba25a13b1ff84e1762305c2a5a1afad794261bdfd182539
Recreated TZX SHA-256: 2d58eded274c56c72ee7ce88a4d2387e3796fe70b4b1fe1701cdab389af40aff
Regenerated BASIC SHA-256: 20dbe5e9cd3afdd231061951cc5b36a1742844b1eebe6ca30c05381ab9d37de3

From the repository root:
  sh src/bonus/Granada-Publishing/20-spectrum-smalltalk/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
