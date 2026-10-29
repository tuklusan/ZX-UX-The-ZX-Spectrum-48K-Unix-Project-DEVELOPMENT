# Moonlander: real native crash and replay (2026-10-29 UTC)

The unchanged published `50-moonlander.ssx` ran inside the ZX-UX 48K Z80
emulator, with the original ROM and the release-identical ZX-UX system tape.
Actual keyboard events advanced the original BASIC game's start, engine-off,
crash, and restart logic. We did not edit any game input, SSX, ROM, kernel,
or framebuffer.

`tests/test_native_moonlander_crash_replay.py` passed one real-emulator test.
The same active native process remained responsible for the screen throughout.
The game did not exit to the shell, and no landing or victory was tested.

Sequence, using `rvm.run_kernel(..., frames=450)` and `run.frame()`:

1. Intro: row 2 `MOON LANDER`; row 21 `Press any key to start`.
2. Type `a`, advance 250 frames; row 0 shows `Height`, row 2 shows `Fuel`.
3. Type `o` (original BASIC line 220), advance 600 frames; row 11
   `YOU HAVE CRASHED`, row 15 `PRESS ANY KEY TO RESTART`.
4. Type `a`, advance 350 frames; height and fuel are visible again;
   the crash and restart prompts are gone. The game remains active.

Each screen was read from the actual 6,912-byte Spectrum framebuffer.
The original ROM font decoded the checked text. Both PNGs were written
straight from the emulator framebuffer with `rvm.write_png`.

| File | SHA-256 |
| --- | --- |
| Original BAS | `7e030c7b674ec6f129d3586e8bb0594d3e1cb2d38d8376460eead4ae69470d68` |
| Original TZX | `4d611258a8d9dde845b4753ede0208724d0e2c3c3baed361a1afd677cea09834` |
| Published SSX | `fb0d3ffccea077340b6644ad4d0ec740ff435324dd157a790ee90ad2156762c4` |
| System TZX (built and frozen) | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| 48K ROM | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| `moonlander-crashed.png` | `93537d568e06244d4435a5c1237453a4fc5138cf0fcc30630ebb114b7c54a235` |
| `moonlander-restarted.png` | `c8ed9253b8cf474a253d831d16236158c9ee22ab7724ca2899725fee8df204a5` |

To reproduce with the repository's checked `build/out/ZX-UX.tzx`, matching
`kernel.json`, recovered `build/tmp/rbc-recovered/rbc/font32.bin`, and
original `dist/zx-ux/tzx/ZX-UX.tzx`:

```sh
RBC_MOONLANDER_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_moonlander_crash_replay.py -v
```

This confirms **one complete losing round and a new playable round** for
Moonlander. The wider 34-game screen-response result remains separate;
complete gameplay for every published game is still unproven.
