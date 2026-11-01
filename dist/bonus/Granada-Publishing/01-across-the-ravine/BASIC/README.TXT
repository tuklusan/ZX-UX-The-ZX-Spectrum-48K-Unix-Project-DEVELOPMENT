Across the Ravine — Granada Publishing

Original media preserved byte-for-byte from the uploaded Granada archive: Ravine.tzx and AcrossTheRavine.tap. The clean 130-line Ravine.bas was independently decoded from the original TZX using the existing verified ZX Spectrum 48K ROM LLIST converter. The program moves men across a ravine and tracks men left, across and lost.

Original BASIC (lines 5000–5010) waits for any key, then attempts the action. The genuine Fuse 48K replay loads the unmodified tape using the emulator's --auto-load option and performs two real SPACE key presses. The second screen shows the number of men changed after an unsuccessful crossing. Both screenshots are genuine live emulator captures, not archive images. Neither an SSX nor a native compile was created. bin/ remains empty.

Reproduce from repo root: sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/01-across-the-ravine/BASIC/REPLAY.sh. Needs Fuse SDL, Xvfb, Pillow, python-xlib.
