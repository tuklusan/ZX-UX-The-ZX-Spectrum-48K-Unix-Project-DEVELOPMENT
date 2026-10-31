25-colonyinv--ColonyInv
Original untouched Spectrum 48K snapshot: ColonyInv.z80; original TZX: ColonyInv.tzx. Clean BASIC listing independently decoded directly from original TZX with the existing ROM LLIST converter.

Defend the colony; the emulator shows Score and High, moving player objects and score changes during play.
Original listing controls: 8 moves the player right (line 530), 5 moves left (505), 6 and 7 change a second movement value (510,520).
Two PNGs are actual Fuse 48K emulator captures after live keys 8 and 5, not archive screenshots. A short session does not prove winning or a full playthrough.

Reproduce from repository root: sh src/assets/basic-src/original-sinclair-basic-collections/www.thespectrumshow.net/25-colonyinv--ColonyInv/BASIC/REPLAY.sh. Requires Fuse SDL, Xvfb, Pillow and python-xlib. bin/ remains empty.
