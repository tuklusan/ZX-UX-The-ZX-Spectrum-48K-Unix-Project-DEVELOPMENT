BOXING — THE SPECTRUM SHOW

We kept the original Boxing-Spectrum.z80 and Boxing4.z81 snapshots from the supplied collection. The archive also contains a derived TAP and TZX, which we label as recreated tapes rather than original downloads. We used the existing ZX-UX 48K ROM listing tool to recover 162 BASIC lines from the recreated TZX. The archived text export differs in control-character spelling; we kept the ROM-derived listing and the original snapshots unchanged.

Boxing is a two-player-style boxing program. The on-screen instructions show 5 for left, 8 for right, and 0 for punch. We opened the original Z80 snapshot in Fuse 48K, pressed p, entered a name, and pressed 5, then 8, then 0. The live ring shows the boxers at changing positions. This confirms a short input-driven game sample, not a full fight or victory. We saved the three Fuse pictures and a replay script. There is no native output in bin/.

Original Z80 SHA-256: 82200f16f0f49141717c6b508ca93f24c62a9be7ac4be471ff9a2b867e6f6f0a
Original Z81 SHA-256: ef24d6a80bd5e3008cdabbea9fc5321527349481a601f331e1af72a5ffd99214
Recreated TAP SHA-256: 04d17121c0e900175c5905baa1bb07bd628a7343844dea31315bdf56020627ad
Recreated TZX SHA-256: 824679ce4a45730f8082e035f03583559b8db617535877f626d08a8a7e713d3b
ROM listing SHA-256: 711f95d733617e8d9f5363c153b1277d4b841afa8c7d4ef6c3cf296b80cf9cf9

Run from the repository root:
  sh src/bonus/www.thespectrumshow.net/26-boxing--Boxing-Spectrum/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the 48K ROM are required.
