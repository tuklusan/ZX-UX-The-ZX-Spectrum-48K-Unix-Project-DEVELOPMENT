BOBSLEIGH — GRANADA PUBLISHING

The original ZX Spectrum 48K tape is Bobsleigh.tap. We kept its bytes as found in the Granada Publishing ZIP. The two TAP copies in that ZIP match exactly. The tape has one BASIC header and one data block. Its 1,675-byte data area holds 1,604 bytes of program text and 71 bytes of stored values.

Bobsleigh-recreated-tape.TZX is the copy supplied inside the ZIP's BASIC folder. It is a later tape copy, not the original TAP. Its 1,604 program bytes match the matching section of the original TAP, byte for byte. Bobsleigh.bas has 63 numbered lines, regenerated from that TZX with the ZX-UX ROM LLIST tool. Spectrum control codes in the text use braces; the original tape holds the exact bytes.

The player steers a red sled between two dark track edges. The game asks for a difficulty from 1 to 5. The on-screen BASIC code reads 5 to steer left and 8 to steer right. Steering into a track edge ends the run. The course is random, so separate plays can differ. The old machine likes to keep its options open.

REPLAY.sh loads the untouched TAP in Fuse 1.6.0, chooses difficulty 1, then plays left and right. The two PNG files in SCREENSHOTS come from that live Fuse session. The sled moves to the right between the views. This is a short play sample, not a complete winning run. No compiled native file is included; bin/ stays empty.

Original TAP SHA-256: 4ef5149f4190621f71cfe32517fee7b07e615ccdd3f4b03cbe1074befcc84baf
Original TAP bytes: 1700
Recreated TZX SHA-256: d803d4ab12d064d3890980e5ec6974e202d249d6db9f528ca370e3e0a70a0991
Recreated TZX bytes: 1645
Regenerated BAS SHA-256: 9951442dca08be3b963b2935bb33a2405aed785c2cdacff4a7cc2eccae97323a
Regenerated BAS bytes: 1668

From the repository root, run:
  sh src/bonus/Granada-Publishing/03-bobsleigh/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
