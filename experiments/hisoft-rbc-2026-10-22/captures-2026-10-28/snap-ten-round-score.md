# Snap: ten real timed pictures and the final score (2026-10-29 UTC)

The published `16-snap.ssx` ran unchanged in the real ZX-UX 48K loader
and Z80 emulator. No keys were sent. Its original BASIC picture loop
(lines 210-320) processed ten timed-out images and then followed the
`P=10` end-of-round branch at lines 310 and 400-430.

The genuine framebuffer reported `CORRECT OUT OF:10`,
`YOU HAVE 0 CORRECT OUT OF 10 IN`, `TIME 2000`,
`BEST TIME SO FAR 2000`, and `PRESS<ENTER>FOR NEXT GAME`.
This verifies one complete timed losing round and the recorded score.
It does not prove a correct picture choice, faster play, working INPUT
replay, STOP, or shell return. The published process was still active
at the original INPUT prompt. Nothing in the game, ROM, kernel, RAM,
or framebuffer was patched to obtain the result.

Reproduce on a host with the checked 768-byte native font and the
unchanged rebuilt ZX-UX tape at `build/out/ZX-UX.tzx`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_SNAP_ROUND_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
  experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_snap_ten_rounds.py -v
```

One real-emulator test passed without skipping. The game inputs and
published SSX were compared before and after the run. Loader admission:
SSX file **10,255**; image **9,433**; BSS **3,173**; stack **384**;
image+BSS+stack **12,990** bytes. Both loader bounds are below **14,000**.

| Original input or genuine capture | SHA-256 |
| --- | --- |
| `16-snap.bas` | `bafb27e17cbeb2d437dfa0b00227a5af42a06b2dd80ba335779a5bb4d0545e5e` |
| `16-snap.tzx` | `1c870d0ead54257211bdbd4930da9f58332d18559977ac53bd90bfd9b44ae0d1` |
| `16-snap.ssx` | `3d75bccf2e596364102724ca4bf93eae2dabf39556c8fe09eb6ed72108a2c702` |
| ZX-UX frozen tape | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| Checked native font | `7b8faa46ee8359ea1cf141a85f618f9f3716334495f3c5c107bb1e5cb86cc468` |
| `snap-ten-round-score.png` | `e44785a7b4faed2703634f6d3752e29160a14c441099ecfc8822af651c839bbf` |

The PNG was generated directly from the genuine 6,912-byte Spectrum
framebuffer through `rvm.write_png` and was not retouched.
