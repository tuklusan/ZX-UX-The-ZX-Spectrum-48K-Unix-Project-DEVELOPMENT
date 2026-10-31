TREASURE ISLAND — Granada Publishing collection

We kept the collection's original TreasureIsland.tap unchanged. The archive does not supply an original TZX for this program. We made TreasureIsland-derived.tzx by wrapping the original TAP blocks in standard TZX tape blocks without changing their payloads. The TAP record checksums and the reverse conversion were checked. The Spectrum ROM-based listing tool recovered 240 BASIC lines from the derived TZX. The listing is a text export, not a replacement for the original tape.

The program draws an island map. The listing describes quicksand, hostile natives, pirates, and a marked treasure. The player's movement keys are 5, 8 and 6; H opens help. Our Fuse 48K run loaded the original TAP, started BASIC with R and ENTER, and sent 5, 8 and 6 during the live map scene. Four genuine captures record the map before and after those keys. The map changed, and one captured frame reported hostile natives. We did not find the treasure or finish the game. The treasure is still doing what treasure does best: remaining somewhere else.

REPLAY.sh uses the original TAP, Fuse SDL, Xvfb, the 48K ROM, Python 3, Pillow, and python-xlib. The visible changes followed the documented keys, but random events can also change the screen. No native executable was produced.

Original source SHA-256:
TreasureIsland.tap aa843b4c34713212a590e52e05e8b21df51f9403ad0153eb27ca42dce343d60f
Derived listing and TZX are not original source media.
