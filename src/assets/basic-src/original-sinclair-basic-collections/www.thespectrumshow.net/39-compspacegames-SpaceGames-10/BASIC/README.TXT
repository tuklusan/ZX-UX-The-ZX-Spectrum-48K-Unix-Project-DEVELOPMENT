TRIP INTO THE FUTURE — Computer Spacegames, tenth program

We kept the supplied FUTURE.tap and FUTURE.tzx source bytes unchanged. The complete 15-program SpaceGames source tapes and Info.txt are already stored with SpaceGames-01. We decoded 22 numbered BASIC lines from FUTURE.tzx using the ZX-UX 48K ROM LLIST tool.

The program asks how fast the ship should travel, as a fraction between 0 and 1, and then asks for the trip distance. It prints two elapsed-year figures and compares the arrival with a random target year. BASIC lines 120-160 do the arithmetic; lines 170-220 report whether the trip was close enough or too long.

We ran the original TZX in Fuse 48K. We entered speed 0.5 and distance 20, and saw 40 years for the trip and about 46.188 years for the future arrival. The run displayed NOT EVEN CLOSE, then stopped. We captured the speed question, distance question, and result from the active emulator. The 1982 travel agent would not offer a refund.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. No native output was built.

Source SHA-256:
FUTURE.tap 22d609ff487edd52954d6e5d9908f24e0e0dacc6684bd9b7329e4e37746eee1d
FUTURE.tzx bc6bd6c5152cc6a2093d2a343f1709ee9a54efc6638a2f5661ebd7c2d8192f13
