COMMANDO JUMP — GRANADA PUBLISHING

We kept the original CommandoJump.tap from the Granada Publishing ZIP without changes. The matching copy in original-medium/ has exactly the same bytes. The TAP has a BASIC header and one data block. Its program holds 2,691 bytes of BASIC and 71 bytes of stored values.

CommandoJump-recreated-tape.TZX is a later tape copy supplied in the ZIP. The BASIC program bytes match the original TAP, byte for byte. CommandoJump.bas has 101 numbered lines regenerated with the ZX-UX ROM LLIST tool. The original TAP, rather than the text, remains the source for exact tape bytes.

The game shows a wall and a small jumper. Wait for Ready, Steady, and GO. Press a key only after GO, then press another key during the jump. The source checks the delay and moves the jumper over the wall when the timing works. Pressing too soon is marked as cheating. A good wall deserves a fair try.

REPLAY.sh loads the original TAP in Fuse 48K at 50% speed. Two Space presses create a short live play sample. The PNG views show the moving player and the wall after each action. This run is not a full series of ten jumps or a native build; bin/ remains empty.

Original TAP SHA-256: 7ea6c1d341c5eef2fb77f30615116f7c53f8a96b1fe510c287b6f5d8efe77b6a
Original TAP bytes: 2787
Recreated TZX SHA-256: c77e94581ad31fe4568af473fc8904b219b33c8ef0e3170182a0c1c9e5ace8fd
Recreated TZX bytes: 2732
Regenerated BAS SHA-256: 6b5a85b6518cddd2ce78c6b0dc824219bc1390e35752750975c1af8eb0dfa3ce
Regenerated BAS bytes: 2659

From the repository root, run:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/05-commando-jump/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
