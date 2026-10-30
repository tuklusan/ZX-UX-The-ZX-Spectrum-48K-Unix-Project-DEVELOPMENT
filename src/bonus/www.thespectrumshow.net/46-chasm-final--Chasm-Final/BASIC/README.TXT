46-chasm-final--Chasm-Final
Original untouched Spectrum 48K snapshot: Chasm-Final.z80; original TZX: Chasm-Final.tzx. Clean BASIC listing independently decoded directly from original TZX with the existing ROM LLIST converter.

The screen shows an active side-scrolling red chasm, score, remaining lives and a small ship. Screens are genuine Fuse input captures after steering left and right.
First press M to view the second page of instructions, then P to start. Original listing controls: O moves left and P moves right (line 290); S and X steer vertically (line 295); A fires (line 990).
Two PNGs are actual Fuse 48K emulator captures after live keys o and p, not archive screenshots. A short session does not prove winning or a full playthrough.

Reproduce from repository root: sh src/bonus/www.thespectrumshow.net/46-chasm-final--Chasm-Final/BASIC/REPLAY.sh. Requires Fuse SDL, Xvfb, Pillow and python-xlib. bin/ remains empty.
