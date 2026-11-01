BUG EYES — Computer Spacegames, fourth program

The Spectrum Show collection includes the program-specific BUG.tap and BUG.tzx. Both are kept byte-for-byte from the supplied archive. The original 15-program SpaceGames tape and its Info.txt are already stored with SpaceGames-01. The 39 BASIC lines in BUG.bas came directly from BUG.tzx through the ZX-UX Spectrum ROM LLIST tool; no lines were added.

The program shows two eyes, OO, at one of four screen positions. The player presses 1, 2, 3, or 4 while the eyes are visible. A matching number scores a hit and displays an asterisk. After ten turns the program reports how many bugs were hit (BASIC lines 30-230).

We loaded BUG.tzx in genuine Fuse 48K, ran the game, pressed number keys during its short turns, and saw both the eyes and the hit marker. SCREENSHOTS contains live Fuse frames before and after numbered input. REPLAY.sh repeats the key attempts and saves fresh images. These short sessions do not claim a perfect score or a full ten-turn result.

To replay: run BASIC/REPLAY.sh from this folder. The script needs Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM. No native executable was built.

Source SHA-256:
BUG.tap 13145a776c3b3420112ed4d9058587f0fb0ebc78f5df3de753e2979e21aa9b3f
BUG.tzx 1d1f133ce6a7e82d504a4ebb6ce04190c0f606f38e4976cca582926696677e8a
