DEATH VALLEY — Computer Spacegames, eleventh program

We kept the supplied VALLEY.tap and VALLEY.tzx bytes unchanged. The original 15-program SpaceGames source tapes and Info.txt are already with SpaceGames-01. We recovered 44 numbered BASIC lines from the program-specific TZX using the ZX-UX 48K ROM LLIST tool.

The program asks for a valley width, then prints lines with two walls and a player star. BASIC lines 240-300 read Q and P as opposite steering controls. The path shifts during the scrolling run. Lines 310-390 check for a crash or reaching the finish.

We loaded the original tape in Fuse 48K, entered width 10, and sent Q and P while the valley was scrolling. Genuine Fuse screen captures show the width prompt and several printed rows before and after those keys. The automatic path changes also move the walls, so the images do not prove a particular steering displacement. We did not confirm a complete run or a crash. That is a surprisingly calm day in Death Valley.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. We built no native game file.

Source SHA-256:
VALLEY.tap 4dc8c7d9478719ca4dcbeae31804e0000b1e523f992272253745411dc1e11e41
VALLEY.tzx 97406c364a80927c6957417ef7c400f422725ccc22fe1b268eb6a642f8855e9e
