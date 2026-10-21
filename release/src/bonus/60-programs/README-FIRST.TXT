SPECTRUM 60 - CLEAN EDITION v22
SANYALnet Labs  |  Sinclair ZX Spectrum 48K

The sixty programs from the book have their own numbered folders.
We kept each non-auto-run TZX tape, the matching BASIC source,
and the selected genuine FUSE screenshots. The v21 cleanup left us
with 155 images worth keeping. We have not touched a single pixel.

WHAT TO FIND
All 60 programs live directly under release/dist/bonus/60-programs/.
Each numbered folder has a BASIC/ and a C48/ sibling:
  BASIC/ Original .bas and .tzx files, instructions, replay scripts,
         and genuine original BASIC SCREENSHOTS/.
  C48/  src/ for converted C48 source files, bin/ssx/ for native ZX-UX
         SSX programs, and bin/tzx/ for their ZX-UX TZX tapes.
         screenshots/rvm/ and screenshots/fuse/ are for captured results.
         For now these C48 folders contain only .gitkeep placeholders.
Some BASIC folders also contain REPLAY-INTRO.sh.
The original BASIC sources and tapes, and all reference PNGs, are intact.

HOW TO START A TAPE
Attach the TZX file in the Spectrum 48K emulator. Type LOAD "",
press Enter, and wait until loading finishes. Then type RUN and
press Enter. These tapes do not start the program automatically.

HOW TO REPLAY THE CAPTURES
From a program's BASIC/ folder on a supported Linux host, run sh ./REPLAY.sh.
The scripts use FUSE, Xvfb, Python 3, Pillow, and python-xlib.
The bundled setup can unpack the included FUSE packages when needed.
Fresh screenshots appear under REPLAYS/ at the collection root.
Read the program's KEYS-AND-TIMING.TXT for the exact recorded keys,
wall-clock times, and original source captures. Different timing
and random states can make a later run look slightly different.
The machines are consistent. Their timing is less sentimental.

CHECKING THE TAPES
Run python3 TOOLS/verify_nonautorun.py from the collection root.
It checks the sixty revised TZX files against the original TAPs,
allowing only the BASIC auto-start header setting and checksum to
change. It does not test the behavior of the BASIC programs.

INDEX.csv lists the programs, BASIC/ filenames, images, and tape hashes.
CLEAN-INDEX.json holds the image source records from v21.
CLEANUP-SUMMARY.json records the earlier screenshot cleanup.
SHA256SUMS.txt lists hashes for files inside this edition.
The previous v21 ZIP remains a separate copy; we have not altered it.

FOLDER LAYOUT (C48 PORTS NOT YET CREATED)
  release/dist/bonus/60-programs/
    01-minelay/
      BASIC/01-minelay.bas
      BASIC/01-minelay.tzx
      BASIC/SCREENSHOTS/
      C48/src/.gitkeep
      C48/bin/ssx/.gitkeep
      C48/bin/tzx/.gitkeep
      C48/screenshots/rvm/.gitkeep
      C48/screenshots/fuse/.gitkeep
    02-fall-guy/
      ...

PROGRAMS.zip is a convenience copy of the 60 numbered folders.
Use relative paths under this collection root for replay scripts and
integrity verification tools. All SHA256SUMS.txt paths are relative to
release/dist/bonus/60-programs/.

No C48 source, SSX, TZX, runtime screenshots, or verification results
have been created. Original BASIC .tzx must not be confused with future
C48/bin/tzx/ programs. This change only reorganizes the collection.
