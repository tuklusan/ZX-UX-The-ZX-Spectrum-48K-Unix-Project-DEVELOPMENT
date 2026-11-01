COMPUTER CHOICE — sound routine 6

This is routine 6 of seven Computer Choice programs in the Spectrum Show collection. The untouched original full CompChoice TAP is stored with routine 1. The supplied single-program List6.tap and List6.tzx are kept unchanged. We decoded List6.bas from the TZX using the ZX-UX ROM LLIST reader.

This sound routine writes machine-code bytes into memory. It uses POKE, RANDOMIZE USR and PAUSE in a repeating sequence. The source gives one numeric value as a way to change the tone, but has no player controls or screen graphics. We ran the supplied tape in Fuse 48K and captured the result. Audio was disabled, so no heard tone was verified.

The source has six numbered BASIC lines, including a RETURN from the sound subroutine. It repeats the cycle with GO TO 40.

REPLAY.sh uses Fuse SDL, Xvfb, Python 3, Pillow and python-xlib. No native build was made.

Source SHA-256:
List6.tap 7d83e244ebdec8083f65b733d5f3631e33a579eab199ec06531911ed26fab8c5
List6.tzx 102d6406d193483473faa2f5b39145eb9f09e54404258cf0dd0207cef53077b0
