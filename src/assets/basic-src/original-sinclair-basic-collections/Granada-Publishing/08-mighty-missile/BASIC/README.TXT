MIGHTY MISSILE — GRANADA PUBLISHING

We kept the original MightyMissile.tap from the Granada Publishing ZIP. Its second original copy has the same bytes. The BASIC part contains 3,260 program bytes and 597 stored bytes. We kept the later TZX from the ZIP as well; the BASIC program bytes match those in the original TAP. MightyMissile.bas has 128 numbered lines regenerated through the ZX-UX ROM LLIST tool.

The player defends a shield against attackers moving across the field. The BASIC source reads 5 and 8 to shift the missile position left or right. A move also starts a missile. The screen displays shield strength, the attacker number, and hits. A careful move can help, though the attackers have other ideas.

REPLAY.sh loads the original TAP in Fuse SDL 1.6.0 at 50% speed and presses 5, then 8. Three real game views show the field, moving craft, and missile actions. We checked the changing pictures directly. These screenshots are a short sample rather than a complete defense or a native build. No compiled file is included; bin/ remains empty.

Original TAP SHA-256: 81a478c98eba45618a641b3b83d3e9dc908c6efb763c6ed1624c5df7bfb1c18f
Original TAP bytes: 3882
Recreated TZX SHA-256: dea858fab10c315665a0d0550279213d17947f119dc9ba6f9396006a8e9276b7
Recreated TZX bytes: 3301
Regenerated BAS SHA-256: a35c254e93cb92f2ee544eacdc213082e541c5ddfcb592e8326ba8b73223f96a
Regenerated BAS bytes: 3387

From the repository root, run:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/08-mighty-missile/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
