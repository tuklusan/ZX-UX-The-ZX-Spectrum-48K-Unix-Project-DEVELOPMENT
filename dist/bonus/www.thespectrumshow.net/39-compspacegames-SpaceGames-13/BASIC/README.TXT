MINES — Computer Spacegames, thirteenth program

We preserved MINES.tap and MINES.tzx exactly as supplied. The original 15-program SpaceGames tapes and Info.txt are already with SpaceGames-01. We recovered 72 numbered BASIC lines from MINES.tzx using the ZX-UX 48K ROM LLIST converter.

The program runs a mining colony. Each year, it asks how much ore to sell, how many mines to sell, how much money to spend on food, and how many mines to buy. Cash, mines, population, ore, and satisfaction can change. The source includes accidents, labor trouble, and a ten-year term. Being in charge turns out to involve arithmetic.

We loaded the source TZX in Fuse 48K, sold 10 tons of ore, sold one mine, spent $2000 on food, and bought no new mine. Fresh Fuse screenshots show the four input steps and the transition from YEAR 1 to YEAR 2. The changes were visible in cash, mine count, ore, population, and satisfaction. This was a single completed business year, not a full ten-year game.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. We built no native output.

Source SHA-256:
MINES.tap 3f983bc6f39301085fcb466c10db9ebc8fbf24c2f7ee838d3f01fc434097c3d1
MINES.tzx 2861a3dc3c4c0536706b57dab0dad9a7a147c62a5127c19d08491b2fc3cf4c67
