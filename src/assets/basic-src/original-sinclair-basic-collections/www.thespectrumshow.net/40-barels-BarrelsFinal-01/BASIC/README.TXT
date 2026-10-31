BARRELS AND LADDERS — D. Millington, 1983

We preserved the original Barrels.tap and Barrels.tzx bytes unchanged. The original medium contains the same TZX tape. We recovered 104 numbered BASIC lines from the TZX using the ZX-UX ROM LLIST tool.

The original listing draws a multi-level platform game with ladders, moving obstacles, three lives, a timer and score. BASIC line 120 reads 5 and 8 as opposite horizontal moves. Line 135 reads 0 to use a ladder when the player is on one. The game restarts after a lost life or round with an any-key prompt.

We loaded the original TZX in Fuse 48K, reached the moving platform board and pressed 5 and 8. Live Fuse captures before and after those keys show a changing game. The obstacles also move on their own; the screenshots do not isolate the player's exact position. We did not confirm a complete stage or a win.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow and python-xlib. There is no native binary output.

Source SHA-256:
Barrels.tap  4998688e58bcadcb8da223344f6b7ac6918ebf464addb97699aeddb492140dff
Barrels.tzx  63eb4bc47fe06e4ebcdc9af7c3dd685d2a485d522e79071f21eedaa9d8519006
