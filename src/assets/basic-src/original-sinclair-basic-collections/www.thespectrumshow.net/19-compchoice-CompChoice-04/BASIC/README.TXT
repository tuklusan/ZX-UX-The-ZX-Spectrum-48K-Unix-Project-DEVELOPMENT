COMPUTER CHOICE — sound routine 4

This is routine 4 of seven Computer Choice programs in the Spectrum Show collection. The untouched original full CompChoice TAP is stored with routine 1. The supplied single-program List4.tap and List4.tzx are kept unchanged. We decoded List4.bas from the TZX using the ZX-UX ROM LLIST reader.

This sound routine writes a short machine-code sequence into Spectrum memory. It varies values in a descending loop and calls the routine. An extra NEXT and a jump to line 50 follow in the source. No screen picture or player keys are provided by the BASIC source. We ran the original tape in Fuse 48K. The live pictures show BASIC before and after RUN, but do not demonstrate any sound. There is no documented win condition.

The source has seven BASIC lines and uses POKE and RANDOMIZE USR. Program flow after the first descending loop is shown exactly by the supplied listing; this brief run is not a proof of endless playback.

REPLAY.sh uses Fuse SDL, Xvfb, Python 3, Pillow and python-xlib. No native build was made.

Source SHA-256:
List4.tap b77d357d4b25853fcc66f0d77c2dfc0ed4e66b3cc4cde66d74584c1cf7f3e8aa
List4.tzx cf61e2ff28e7bc9f1e7a573182d3b24926e073c6d00a25860e79acdd90fd5dbf
