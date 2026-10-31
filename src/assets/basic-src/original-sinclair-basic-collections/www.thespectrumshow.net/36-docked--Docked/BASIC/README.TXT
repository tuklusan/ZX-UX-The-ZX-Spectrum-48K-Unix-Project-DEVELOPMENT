36-docked--Docked
Original untouched Spectrum 48K snapshot: Docked.z80; original TZX: Docked.tzx. Clean BASIC listing independently decoded directly from original TZX with the existing ROM LLIST converter.

Two-stage docking game. At the original snapshot the screen says GAME OVER and Y/N; entering Y restarts an active game with score and fuel. Key presses change the live ship and hazards.
Start from the GAME OVER prompt by pressing Y (verified). Original listing controls: 8 and 5 are horizontal controls at line 1320, 6 and 7 steer vertically at lines 1310 and 1335.
Two PNGs are actual Fuse 48K emulator captures after live keys 8 and 5, not archive screenshots. A short session does not prove winning or a full playthrough.

Reproduce from repository root: sh src/assets/basic-src/original-sinclair-basic-collections/www.thespectrumshow.net/36-docked--Docked/BASIC/REPLAY.sh. Requires Fuse SDL, Xvfb, Pillow and python-xlib. bin/ remains empty.
