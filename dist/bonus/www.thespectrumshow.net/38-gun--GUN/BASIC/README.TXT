GUNFIGHT — Mark Hinchcliffe, Spectrum Show GUN

The original collection contains a GUN.z80 snapshot and separate TAP and TZX files. All three media files remain byte-for-byte unchanged. We also kept the collection's 117-line ROM LLIST BASIC export, independently checked against the TZX with the repository converter. The BASIC listing includes machine-code data, POKEs, and USR calls. A saved snapshot is more than a title screen with excellent intentions.

The original Z80 opens on the BASIC editor. In Fuse 48K, press R then Enter to RUN, allow the long setup, and use Space at the instructions screen. Press 1 for level one. The game shows a Western scene with a movable gunsight, bullets, lives, and score. Lines 5430 and 5440 describe cursor keys 5, 6, 7, and 8, plus 0 to shoot. We saw the gunsight shift left and right after 5 and 8, and the ammo strip changed after 0. No full round, target hit, or win was confirmed.

We saved the displayed Fuse frames as PNGs in SCREENSHOTS/. They came from this play session, not the website. The replay uses Fuse, Xvfb, the 48K ROM, Python 3, Pillow and python-xlib. We made no game executable.

Original archive SHA-256:
GUN.z80 283979e2309c6b5dcd22c367b367a5802e4d408230f3191fb629de7fc7b6c298
GUN.tap 848c8906393526a494965904ac742b2959a6cb5eefe2f30636fc8cf89323ef77
GUN.tzx 54716d01512ba259f4230f72dcaa4e4a86b5055ebda4e895be76a5d51382d147
GUN.bas ce7f7683ca2bec6520eedc91dc57639c91a445e91fbab8a0300e68717d840ac6
