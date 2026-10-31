COMPUTER CHOICE — sound routine 5

This is routine 5 of seven Computer Choice programs in the Spectrum Show collection. The untouched original full CompChoice TAP is stored with routine 1. The supplied single-program List5.tap and List5.tzx are kept unchanged. We decoded List5.bas from the TZX using the ZX-UX ROM LLIST reader.

This sound routine writes a short machine-code sequence into Spectrum memory. The BASIC cycles values from zero through 255, calls RANDOMIZE USR, and repeats. It has no player keys, screen picture or winning condition. We loaded the original tape in Fuse 48K and captured the screen before and after RUN. Audio was disabled, so sound could not be checked.

The six-line BASIC program has a loop that returns to line 50. No player action is required after RUN.

REPLAY.sh uses Fuse SDL, Xvfb, Python 3, Pillow and python-xlib. No native build was made.

Source SHA-256:
List5.tap a240edb7b2652b919cd6f8674c82e4a32fc3890d751401b19bbf7de4c0c2827e
List5.tzx a235c1ba33cd8f4eb8002efd1db70dfa13ef61124d44db6b676df32e93057c86
