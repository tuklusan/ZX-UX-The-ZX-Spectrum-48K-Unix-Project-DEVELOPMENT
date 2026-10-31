POOJAN — original Spectrum Show snapshot

We kept the original poojan.z80 bytes from the supplied collection.
The supplied TAP and TZX are later recovered versions, not the original
website media. We decoded the TZX into 285 numbered BASIC lines using
the ZX-UX 48K ROM LLIST converter. The tape is separate from the snapshot.
The BASIC contains graphics setup, the menu, action controls and game code.
We did not claim that the tape restores every byte of the snapshot.

We started the original Z80 in Fuse 1.6 in Spectrum 48K mode. Its control
screen says A for UP, Z for DOWN and SPACE for FIRE. Pressing a key starts
play after the first stage screen. We recorded real gameplay and confirmed
vertical player motion from Z followed by A. SPACE changed the view, but
we did not confirm a hit, a full round, or a winning score.
The PNG files come from live Fuse captures, not the source ZIP.

Original and recovered media SHA-256:
poojan.z80  1ffa6d4991fae506c8314cd58a4103fd87432ad9d6a2e7ceaf78bf1c2b15c121
poojan.tap  e7d13526c63ae8c0792ead9124171a84a3cbc9e36cb236ef3d48bb230d40dc7a
poojan.tzx  61c3bad44f8e94918767235840b8ff591dc3a836673e1830d6ef3cd2e3e2f39b

The 285-line listing is derived from the recovered TZX.
Run ./REPLAY.sh with Fuse SDL, Xvfb, Pillow and python-xlib.
The replay uses the ZX-UX 48K ROM. No native SSX build was made.
