GALACTOIDS — original Spectrum Show snapshot

The source archive includes the original Galactoids.z80 snapshot. The supplied TAP
and TZX files are later recovered tape versions, not original website tapes.
The three-line Galactoids.bas listing comes from the supplied TZX by the ZX-UX
48K ROM LLIST converter. It loads a separate 1,428-byte CODE block at 31000
and runs it. It is not a full BASIC version of the arcade program.

We opened the original Z80 in Fuse 1.6, chose the on-screen ENTER start,
and played using the on-screen Z, X and SPACE controls. The white player
ship moved left after Z and right after X in live screen captures. SPACE
was sent and a later screen changed; we did not confirm a hit or a win.
The screenshots are fresh Fuse views, not images from the supplied ZIP.
We did not verify every part of the recovered code or finish a round.
The older BASIC data listing in the source archive was not independently
recovered from the resident snapshot and is not presented as a proven tape listing.

Source media hashes (SHA-256):
Galactoids.z80  fabf424697d178fa573f3d0c5dfbc8bd9d8a0c26a34f6d768e7d393625f13526
Galactoids.tap  1a7d6420e500b831d7a8be261382370bb7598c3e2ba90dcdd987d4693f342144
Galactoids.tzx  3fe9b55e7290e12bb90ad8eb337fddd99dcd143c24a8e824a3d8872ff3522330
Galactoids-GALCODE.bin  6eb29e32c72fd36e2b9a3f5662691e30292f85f45058ea6b9db5fc7b8155d870

Run ./REPLAY.sh with Fuse SDL, Xvfb, Pillow and python-xlib installed.
The normal ZX-UX 48K ROM is used. No native SSX output was built.
