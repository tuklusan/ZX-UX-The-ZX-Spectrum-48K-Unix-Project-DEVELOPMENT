16-rockattackfix--RockAttackFix

Original archived Spectrum 48K game snapshot: RockAttackFix.z80
Snapshot SHA-256: aa6c028fd76fbdcdcba84e37106757bc6cd23456583b82634a0f88efcc49c5ed
Archive-derived tape: RockAttackFix.tzx
TZX SHA-256: 4cef42a576e47e256199802fc7f8cfbadb8990d5b95f74566fd49aa2026289da
Verified BASIC listing independently decoded with build/tools/zx-tzx2bas.py.

Start from the instructions, rotate the ship, thrust and fire on the asteroid playfield.
The unchanged .z80 original is loaded in genuine Fuse 48K; the replay
records actual screenshots after real keyboard input. Two images document
a short game session, not a full playthrough or native compilation.

Run: sh BASIC/REPLAY.sh (Fuse SDL, Xvfb, Pillow, python-xlib required).
See KEYS-AND-TIMING.txt for controls and replay steps.
bin/ remains empty for future builds.
