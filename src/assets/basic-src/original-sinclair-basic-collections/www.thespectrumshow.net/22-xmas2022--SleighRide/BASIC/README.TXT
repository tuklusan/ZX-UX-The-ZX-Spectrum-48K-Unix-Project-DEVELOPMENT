SLEIGH RIDE — Spectrum Show Christmas collection

We kept the source collection's Z80 snapshot, TAP and TZX without changes. The TZX contains 57 numbered Sinclair BASIC lines. We recovered the listing with the Spectrum ROM-based tape listing tool; a separate tape record scan confirmed 57 lines in order.

The program draws a sleigh and reindeer against a blue night sky, with stars and a yellow moon. Its BASIC source makes character graphics, draws the scene and plays a sequence of BEEP tones. The animation advances without player input; there are no move keys to test. The reindeer handle the journey without asking for directions.

We loaded the original TZX in Fuse 48K, entered RUN, and captured three frames while the drawing changed. These PNGs come from the running Fuse screen, not from the collection's reference images. The session did not record sound or prove a full animation cycle. REPLAY.sh gives the actual waits and startup inputs. No native game was built.

The replay needs Fuse SDL, Xvfb, the original 48K ROM, Python 3, Pillow and python-xlib.

Original source SHA-256:
SleighRide.z80 14321d2d43d020697bd4fc4126252f05dd78968cabf43da6f4774ea3819d407d
SleighRide.tap de0562f9efb8549d4451d8904a5cb505d6fcd577a40c95648fd7b3387493b4ff
SleighRide.tzx 025811da65788db35a620bb9c1089773e3bd7d1c5fdc018d520999b7775c5f0c
