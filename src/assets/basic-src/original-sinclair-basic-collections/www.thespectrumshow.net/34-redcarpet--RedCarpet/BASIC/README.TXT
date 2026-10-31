RED CARPET — original Spectrum Show snapshot

We kept the original RedCarpet.z80 snapshot from the supplied archive.
It describes itself as a 16K Spectrum game. The 48K Fuse machine ran that
snapshot for this test. The supplied archive also holds recovered TAP and TZX tapes,
not original website tapes. We retain its TZX and the original snapshot. The ZX-UX 48K ROM LLIST converter recovered
52 numbered BASIC lines from the TZX. The source media were not changed.

The game opens with a stop-the-tape prompt. We pressed SPACE to view the
instructions, then S to start the maze. The program names Z for LEFT,
X for RIGHT, C for DOWN, and F for UP. We sent F, saw the white character
move up, then sent Z and saw it move left. The score changed while the
red carpet was drawn. Reversing into the trail can end the round.
We did not finish the maze. The new 01-STOP-TAPE through 05-AFTER-LEFT
PNG images were captured in Fuse. Older Fuse captures remain untouched.
No screenshot was taken from the source ZIP.

Source media SHA-256:
RedCarpet.z80  4aa9978cad8290757df7c03da205a4a8aafcc9eb961174be8d214ead747e55f8
RedCarpet.tap  4bb66c4134bfe8f564f5747f9a47de2b65e7979286f06b8d0a060c10a6f8d297
RedCarpet.tzx  17464d83f74f5fa6b135c767d0c41405381c4fa0fcc52fa495f3660ac5ae0392

The original Z80 is the tested starting point; the recovered tape may not
retain every byte of the saved machine state.
Run ./REPLAY.sh with Fuse SDL, Xvfb, Pillow and python-xlib.
The replay uses the ZX-UX 48K ROM. No native SSX output was made.
