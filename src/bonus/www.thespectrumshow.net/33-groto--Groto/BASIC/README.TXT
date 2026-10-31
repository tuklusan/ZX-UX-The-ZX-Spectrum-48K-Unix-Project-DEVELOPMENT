SANTA'S GROTO — original Spectrum Show snapshot

We kept the original Groto.z80 snapshot exactly as supplied. The archive's
TAP and TZX are recovered tape copies, not original website tape images.
The three are kept separately. We decoded the recovered TZX with the ZX-UX
48K ROM LLIST converter and checked its 72 numbered BASIC lines.

The original Z80 opened at a BASIC listing. We typed RUN in the Spectrum
editor, then pressed SPACE at the title screen. The program explains that
P moves up, L moves down, Z moves left and X moves right. It asks us to
collect Santa's presents and avoid the guard and walls. After the help
and warning screens, we reached the genuine playing area. We pressed Z
and X and saw the white sledge move left and then right. We did not
finish a level or confirm a collected present. The images under
SCREENSHOTS are live Fuse captures; none came from the source ZIP.

Source media SHA-256:
Groto.z80  d4026e32e1910df95d519a6fe4843317e854370fff050d239c52d1382af41ceb
Groto.tap  2f51e0478b5b449513af3531563872482c719258a71c176665f36f7bfaecfe9a
Groto.tzx  16f020d0aa8fb9f763ab953a5903125a187d45fc959e59ca0f33274ebe7ee86e

The original snapshot is the tested starting point. The recovered TAP
and TZX may lack state that was held in snapshot memory.
Run ./REPLAY.sh with Fuse SDL, Xvfb, Pillow and python-xlib installed.
The replay uses the ZX-UX 48K ROM. No native SSX output was made.
