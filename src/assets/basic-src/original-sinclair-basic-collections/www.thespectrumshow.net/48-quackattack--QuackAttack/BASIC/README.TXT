48-quackattack--QuackAttack
Original untouched Spectrum 48K snapshot: QuackAttack.z80; original TZX: QuackAttack.tzx. Clean BASIC listing independently decoded directly from original TZX with the existing ROM LLIST converter.

Active duck shooter. The original game screen says choose difficulty 1-3, then use M to fire. The two images were captured after two genuine firing inputs, with enemies and shots moving.
Original listing controls: 1,2,3 choose difficulty (source lines 2055-2080); M fires (line 110).
Two PNGs are actual Fuse 48K emulator captures after live keys m and m, not archive screenshots. A short session does not prove winning or a full playthrough.

Reproduce from repository root: sh src/assets/basic-src/original-sinclair-basic-collections/www.thespectrumshow.net/48-quackattack--QuackAttack/BASIC/REPLAY.sh. Requires Fuse SDL, Xvfb, Pillow and python-xlib. bin/ remains empty.
