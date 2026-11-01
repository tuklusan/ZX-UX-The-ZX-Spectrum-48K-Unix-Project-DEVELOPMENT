SPACE RESCUE — Computer Spacegames, fourteenth program

We kept RESCUE.tap and RESCUE.tzx exactly as supplied. The master 15-program SpaceGames tapes and Info.txt are already with SpaceGames-01. We decoded 104 numbered BASIC lines from the program-specific TZX using the ZX-UX 48K ROM LLIST tool.

The game sends medical supplies to a distant planet. The player allocates the ship's energy between engines, life support, and shields. During the trip, the program reports hazards and computes the travel time. A later stage may ask for landing energy if the ship survives the journey. Source lines 140-240 handle the first allocation, and lines 250-840 handle events and arrival.

We loaded the tape in Fuse 48K, answered N to the instruction question, and allocated 100 to engines, 150 to life support, and 150 to shields. We saw the departure and an asteroid-storm message. The screenshots come from the live Fuse session. We did not confirm a landing or a completed trip. Space travel still comes with a fair amount of paperwork, although the ship does not provide a desk.

REPLAY.sh uses Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. We built no native executable.

Source SHA-256:
RESCUE.tap 9d1594a48d553d206222e2581ae2610c502677a2edba9ef3c0540741ad503f81
RESCUE.tzx c8f9f75c0350190372a43c063e06a28a5fc6ae361a04752c40e6c40d8cc1b67b
