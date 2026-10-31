COMPUTER CHOICE — sound routine 7

This is routine 7 of seven Computer Choice programs in the Spectrum Show collection. The untouched original full CompChoice TAP is stored with routine 1. The supplied single-program List7.tap and List7.tzx are kept unchanged. We decoded List7.bas from the TZX using the ZX-UX ROM LLIST reader.

This sound routine writes machine-code bytes into memory, then varies two numbers up and down in repeated loops while calling RANDOMIZE USR. The source has no player controls or changing game graphics. We launched its tape in Fuse 48K and captured a live BASIC screen. Sound was disabled, so the captures do not prove an audible effect.

The seven-line source returns to line 40 for another cycle. The picture is expected to remain blank while the routine runs.

REPLAY.sh uses Fuse SDL, Xvfb, Python 3, Pillow and python-xlib. No native build was made.

Source SHA-256:
List7.tap 721b18ddd4be42ece6a91592c1162e5d94cff1f0c228b3536828547b28f892c3
List7.tzx eed1673e1c18594c102f674d8d35137640f18b0ef8755f7cc4d2175acef197b3
