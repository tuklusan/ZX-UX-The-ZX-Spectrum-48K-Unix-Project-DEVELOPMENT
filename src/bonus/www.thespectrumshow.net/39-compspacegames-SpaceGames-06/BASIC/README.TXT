MOONLANDER — Computer Spacegames, sixth program

We kept the supplied program-specific MOONLAND.tap and MOONLAND.tzx without changing their bytes. The original 15-program SpaceGames tape and Info.txt are stored with SpaceGames-01. The 26-line MOONLAND.bas listing came directly from MOONLAND.tzx through the ZX-UX ROM LLIST tool.

The program asks how much fuel to burn, from 0 to 30 units each turn. It shows time, height, speed, and remaining fuel. The BASIC code calculates a landing or a crash from those choices (lines 70-260).

We loaded the tape in Fuse 48K and entered 0, then 30. The live screen showed height changing from 500 to 447.5, then to 405, with fuel falling to 90 after the second burn. Three PNGs show the first prompt and the views after both entries. We did not land the craft or finish a flight. The Moon, quite reasonably, declined to grade these two attempts.

Use REPLAY.sh with Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM to repeat these inputs and capture the screens. No native executable was built.

Source SHA-256:
MOONLAND.tap c76a480820dbba1ed82c3c8aca837f93638d7f9cb7addedbb358aedf9e2f5409
MOONLAND.tzx e1acc53460bf147d680306639c6f654602b8d8eba20005db3bcd18e0e69c5654
