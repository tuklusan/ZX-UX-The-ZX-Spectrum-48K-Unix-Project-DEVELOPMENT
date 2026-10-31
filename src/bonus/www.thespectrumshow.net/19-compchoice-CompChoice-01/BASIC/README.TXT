COMPUTER CHOICE — sound routine 1

The Spectrum Show collection has seven short Computer Choice BASIC routines. We kept the complete original CompChoice TAP here. List1.tap and List1.tzx are the supplied exports for the first routine, and List1.bas is the eight-line listing decoded from that TZX using the ZX-UX ROM LLIST reader.

This is a sound routine, not a keyboard game. The source writes ten bytes into memory and calls the Spectrum ROM through RANDOMIZE USR. It changes a numeric value in two loops, then reaches a STOP instruction at line 65. We loaded the first routine in Fuse 48K and ran it. The screen showed the STOP result at line 65. No player moves, score, or victory screen exist in this source. The routine also has no reason to display a spectacular spaceship.

Fuse ran with sound disabled, so the images prove loading and the STOP result, not the sound heard on real hardware. The screenshots came from Fuse. REPLAY.sh uses Fuse SDL, Xvfb, Python 3, Pillow and python-xlib. No native executable was made.

Source SHA-256:
CompChoice-original.tap f207e76440506ac96c75bb7b1844dc4714afa4fe35f28d45706a9f05ea804965
List1.tap 81bd85e475c80dece7316a55d8725ab041b2b2f2ab3334db1c167077ac939e84
List1.tzx f30eaf5664f8b5ce9b8bd42a31beb97309fc7276f3971dcdd51b675f1f5d2216
