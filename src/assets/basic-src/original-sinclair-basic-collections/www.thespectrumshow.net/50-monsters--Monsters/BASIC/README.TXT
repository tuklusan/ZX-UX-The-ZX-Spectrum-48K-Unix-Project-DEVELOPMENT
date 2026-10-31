MONSTERS — The Spectrum Show collection

We kept the original Monsters.z80 snapshot and program-specific Monsters.tap and Monsters.tzx without changes. The 115 numbered lines of Monsters.bas were decoded from the original TZX with the existing ZX-UX ROM LLIST tool.

The snapshot opens on a question asking whether to show instructions. Those instructions assign 1 to left, 0 to right and F to fire, which also raises a bomb shield. The goal is to destroy monsters while avoiding bombs and lasers. We chose N, reached the live game and sent 1, 0 and F in Fuse 48K. The saved screens show animated monsters and later a death screen. Changes between frames include independent enemy motion; they do not prove an isolated player movement or a kill. A completed game was not confirmed.

All images in SCREENSHOTS/ came directly from the running Fuse SDL window. REPLAY.sh needs Fuse SDL, Xvfb, the ZX-UX ROM, Python 3, Pillow and python-xlib. We built no native game executable.

Source SHA-256:
Monsters.z80  afffe00836e7fd1a355195d9144020e8e44ac970032885f691d2b580f77cbeba
Monsters.tap  e3d560263a67ec81e85fe7edfc91b0f30f96ceec3eb2a338c169ab6db7aaf86f
Monsters.tzx  747ec19097df79912dee2068a857487bf8cae402f4d1788b2e05fbbdae17aaa1
