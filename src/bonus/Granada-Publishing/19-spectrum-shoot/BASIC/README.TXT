SPECTRUM SHOOT — GRANADA PUBLISHING

We kept the original SpectrumShoot.tap from Granada Publishing. Its first 1,820 BASIC program bytes match the supplied recreated TZX. We regenerated 80 numbered BASIC lines using the ZX-UX ROM LLIST converter.

The game draws a moving bird and a crosshair. The BASIC source reads 5 for left, 6 for down, 7 for up, 8 for right, and f for firing. We pressed 8, then f during a live Fuse 48K session. Both screenshots show the active field. We saw screen changes, but cannot claim a hit from those pictures. No completed five-bird round is claimed.

REPLAY.sh runs the original tape at Fuse speed 200% and repeats these two keys. Images come from Fuse, not from the archive. No native binary is included.

Original TAP SHA-256: dea9e3847f60acbd44b75609f75d9d364152df2a857e972e8386a2d5803915dd
Recreated TZX SHA-256: 4dd812b6acebea044df80578b5f05c8bc143b13571d9a1fd386a33d3857da4b1
Regenerated BASIC SHA-256: 7940ded22ec1a35645480785cb177ddb141da76508e16c70a016660342dfada8

From the repository root:
  sh src/bonus/Granada-Publishing/19-spectrum-shoot/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
