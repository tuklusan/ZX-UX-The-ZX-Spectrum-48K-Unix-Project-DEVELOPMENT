BUG EYES (COLOUR) — Computer Spacegames, fifth program

This is the colour version of Bug Eyes. We kept the supplied program-specific BUGCLR.tap and BUGCLR.tzx byte-for-byte. The original 15-program SpaceGames tapes and Info.txt are stored with SpaceGames-01. The 41-line BUGCLR.bas listing was decoded from this TZX using the existing ZX-UX Spectrum ROM LLIST tool.

Lines 5 and 15 set the screen colours and pause for a key before the round starts. The game then shows yellow OO eyes on a red screen. The player presses 1, 2, 3, or 4 to match one of four possible positions. A successful match displays *. The game reports the score after ten turns, though our short test did not confirm a final total.

We loaded BUGCLR.tzx in Fuse 48K, cleared the starting pause, and entered number keys during the running game. Fresh Fuse screenshots show eyes, another eyes view after two keys, and the hit marker. The captured hit is a single on-screen event, not proof of a finished ten-turn game.

Run BASIC/REPLAY.sh with Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM. No native executable was built.

Source SHA-256:
BUGCLR.tap 818fa9cb45167b8ee55cbabe938ba6491a47374c17eff9cf8481df840bf9dc2b
BUGCLR.tzx 47d1f8d2e56a2e9b2fef07b905b1acc5f86c15de3554de35e2327d090089d896
