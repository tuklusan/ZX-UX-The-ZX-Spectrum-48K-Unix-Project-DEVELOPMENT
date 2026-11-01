DEATH VALLEY (COLOUR) — Computer Spacegames, twelfth program

We preserved the supplied VALLEYCLR.tap and VALLEYCLR.tzx bytes unchanged. The full 15-program SpaceGames source tapes and Info.txt are already with SpaceGames-01. We decoded 45 numbered BASIC lines from VALLEYCLR.tzx using the ZX-UX 48K ROM LLIST tool.

This program uses the same scrolling valley and Q/P steering rules as the eleventh program, but line 5 sets a black screen with colored text. Lines 170 and 230 print the walls in another color. The player star moves between the two walls; touching either wall causes a crash. The input width comes from the starting question.

We ran the supplied tape in Fuse 48K, entered width 10, and sent Q and P while the colored valley scrolled. Genuine Fuse screenshots show the green title, purple walls, and star before and after input. Random wall shifts also change the screen, so the images do not prove an exact steering distance. We did not confirm the finish or a crash. The colorful walls still have very little sympathy.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. No native game output was built.

Source SHA-256:
VALLEYCLR.tap 5adc59fccccecf1683199b610aff169b1e2b0be6eaa217517668ce924bc62991
VALLEYCLR.tzx e5a53806b1b6f84bb8ad7c2af8e9afc33961a530034e246aa6bc43f2b232c0fc
