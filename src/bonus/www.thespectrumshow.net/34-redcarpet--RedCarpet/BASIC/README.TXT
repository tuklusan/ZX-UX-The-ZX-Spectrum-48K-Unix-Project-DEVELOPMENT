34-redcarpet--RedCarpet
Original untouched Spectrum 48K snapshot: RedCarpet.z80; original TZX: RedCarpet.tzx. Clean BASIC listing independently decoded directly from original TZX with the existing ROM LLIST converter.

A 16K Spectrum carpet-laying action puzzle. The real maze is on screen when the controls are used. The run reached the HI SCORE page after collision; it is shown as an outcome, not falsely labeled gameplay.
Original listing controls: Z left (line 170), X right (180), C down (190), F up (200).
Three PNGs record the actual maze before moves, after Z, and the result after X; the final screen may show HI SCORE after a collision. The first two are active maze gameplay. A short session does not prove winning or a full playthrough.

Reproduce from repository root: sh src/bonus/www.thespectrumshow.net/34-redcarpet--RedCarpet/BASIC/REPLAY.sh. Requires Fuse SDL, Xvfb, Pillow and python-xlib. bin/ remains empty.
