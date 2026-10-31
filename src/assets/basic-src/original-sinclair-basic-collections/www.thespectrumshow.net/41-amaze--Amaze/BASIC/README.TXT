AMAZE — The Spectrum Show collection

We preserved the original Amaze.z80 from the source collection. Amaze.tap and Amaze.tzx are tape versions supplied by the archive, rather than original website downloads. A local ROM-style decode recovered 49 numbered lines from the archive's tokenized TZX. The lines are in order. The private text check rejected the unmodified BASIC listing, so we did not publish a separate text listing. The unchanged tape retains every source byte.

A-MAZE-'N' CHASE credits J. Southgate on BASIC line 1. The maze keeps a score and four starting lives. Lines 75, 80 and 90 read keys 5, 6, 7 and 8 for movement. Line 72 checks 0 for a special action that requires a stored item. Line 102 checks P in a separate game condition.

The original snapshot opens on GAME OVER. We pressed Enter to restart, allowed the maze to draw, then pressed 5 and 8. The live Fuse 48K screens show changes in the maze and score. Enemy motion also occurs while keys are idle. No win or full game was confirmed. The images were captured from Fuse SDL, not copied from the archive.

Run REPLAY.sh from the repository root, or run it directly. It needs Fuse SDL, Xvfb, the repository 48K ROM, Python 3, Pillow and python-xlib. No native game was built.

Original and tape SHA-256:
Amaze.z80 af92569f2f4b0cf1a6541fb6ac8761ca18e8ff74e9c8d851591f02afb7214a9b
Amaze.tap efa358cd3d4f393c26a0c1d086d0bf456c60db0d0d1deac98b12b6f71727fb38
Amaze.tzx afa80c66814b3cabe7f8c9c75fe55c8e34ba4be86fa31f3335bc92a48ef54125
