ASTEROID BELT — Computer Spacegames, ninth program

We kept the supplied program-specific ASTEROID.tap and ASTEROID.tzx with their bytes unchanged. The original 15-program SpaceGames source tapes and Info.txt are already with SpaceGames-01. We recovered 33 numbered BASIC lines from ASTEROID.tzx using the ZX-UX 48K ROM LLIST tool.

Ten asteroids appear as star patterns. Each has a random strength from 1 to 9. A numeric key gives the strength of the player's shot. The program reports whether that number is right, too small, or too large, and counts successful shots. Lines 40-320 contain the full ten-round loop.

We ran the program in Fuse 48K and entered strength keys 1 and 3 during visible asteroid rounds. The screen changed as rounds advanced; a successful second hit was not confirmed. The displayed star patterns and later screens are genuine Fuse captures. These few frames do not prove a complete game. The asteroids are entitled to remain skeptical.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. We built no native executable.

Source SHA-256:
ASTEROID.tap 7c304234deab12b2b60e08da6a3b36b2ae5579ad31cb73533e552d4fd9d57204
ASTEROID.tzx a97e4e3ac15baae1f340c49443f54d2c279bd9abbbbc0b5f22fda2bc5577e099
