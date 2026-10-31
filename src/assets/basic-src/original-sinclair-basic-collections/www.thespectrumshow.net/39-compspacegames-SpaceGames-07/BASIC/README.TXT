MONSTERS OF GALACTICON — Computer Spacegames, seventh program

We kept the supplied program-specific MONSTERS.tap and MONSTERS.tzx without changes. The full 15-program SpaceGames source tapes and Info.txt are already with SpaceGames-01. We decoded 45 numbered BASIC lines from MONSTERS.tzx using the ZX-UX 48K ROM LLIST tool.

Four named monsters appear in eight encounters. The game asks which weapon to use: R, S, or T. A choice can kill a monster, have no effect, or cost one member of the five-person group. BASIC lines 180-400 determine the results. We ran the supplied tape in Fuse 48K, entered R and then S, and saw changed monster encounters. This short sample does not prove survival through all eight encounters. We suspect the monsters prefer it that way.

SCREENSHOTS/ contains genuine Fuse screen captures, including the first weapon prompt and the results after the two player choices. REPLAY.sh reproduces the session using Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. We did not build native output.

Source SHA-256:
MONSTERS.tap e3a11c604b71359830f20cd77605acba172dd16617925339623c7be8fa2902f0
MONSTERS.tzx dc49f0fd625a786611d33b456df98f975b32385f6fc2fd19752fc8279a65c98f
