TOUCHDOWN — Computer Spacegames, fifteenth program

We preserved the supplied TOUCHDOWN.tap and TOUCHDOWN.tzx exactly. The full 15-program SpaceGames source tapes and Info.txt are already with SpaceGames-01. We decoded 65 numbered BASIC lines from the TZX using the ZX-UX 48K ROM LLIST tool. BASIC line 10 names Usborne Publishing and the year 1982; we kept that original source line intact.

Touchdown shows a spacecraft descending toward the ground, with gauges for fuel, velocity, height, and thrust. BASIC lines 530-570 read A to raise thrust and D to lower it. The program can report a safe landing, a hard landing, or a lost ship based on speed, height, and fuel.

We loaded the original source in Fuse 48K and pressed A, D, then A during the live descent. Genuine Fuse captures show the moving craft and flight gauges before and after inputs. Background descent continues between keystrokes, so these frames do not alone measure the exact thrust change. We did not confirm a safe landing. The ground remains extremely patient.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. We built no native output.

Source SHA-256:
TOUCHDOWN.tap 5ff20cccb3ee0873bbc7ea18546f5ea0d083e25fbd77871254c9bddf801e7878
TOUCHDOWN.tzx 6f40c00c6ecfb1070f1df230002de391b783c747e2b3b947b2d0d1c5d8a35ebb
