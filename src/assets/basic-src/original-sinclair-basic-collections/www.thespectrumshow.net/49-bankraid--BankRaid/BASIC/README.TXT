BANK RAID — G. Creasey

We preserved the original BankRaid snapshot and the program-specific TAP and TZX bytes. The listing in bankraid.bas contains 50 numbered BASIC lines decoded from the original TZX through the ZX-UX ROM LLIST tool.

The original start screen describes a bank robbery, electronic security and moving obstacles. The on-screen controls are 1 left, 2 right and 0 forward. The listing at lines 330-340 checks these keys. We started the game from the original Z80 snapshot and pressed 1, 2 and 0. The saved Fuse screens show the start prompt, the bank board and later changes while those keys were used. Moving security objects also affect the images, so the exact response to each key was not isolated. We did not finish the game or confirm a successful robbery.

REPLAY.sh runs the original snapshot in Fuse SDL 48K using Xvfb, the ZX-UX ROM, Python 3, Pillow and python-xlib. We made no native game file.

Source SHA-256:
bankraid.z80  98b7dcb445a2a981b013ad52f08f47073ab54c19a651f9efed94d2d2fcc71654
bankraid.tap  ab5e3d4283aae99ad06b30cbbd8f276968267ea63983358a4c15223539069bd2
bankraid.tzx  62393442aa9750bc77a89eeeeae7e911b22643da73997eb692a130d3669a8ac2
