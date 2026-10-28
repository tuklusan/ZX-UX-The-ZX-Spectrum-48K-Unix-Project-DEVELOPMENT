# Two published games — genuine keyboard progression

The original `14-scuba.ssx` and `54-swordsman.ssx` were loaded by the unchanged
ZX-UX 48K kernel and executed in the real Z80 emulator. Original BAS, TZX,
linked SSX, ROM, kernel and other games are untouched.

**Scuba:** The initial source copies the ROM font in a long countdown. A
snapshot at 2,400 frames with no keys shows the original instruction screen,
including `GOOD LUCK...ENTER TO START`. The script waits 1,900 frames, sends
ENTER and later X. At 2,400 frames, the resulting framebuffer shows the
original sea, swimmer and `FISH CAUGHT = 0`. This proves entering the gameplay
screen, not that X movement or fish-catching controls work.

**Swordsman:** A no-key run at 620 frames shows `ANOTHER HERO BITES THE DUST.`
and the original replay prompt. Pressing uppercase Y after a 550-frame wait
shows a new opponent and `TOTAL POINTS=1` at frame 620. The lowercase key was
not observed to replay in a separate probe. This proves one natural loss and
one native Y-replay step, not a complete victory or every combat strategy.

Both programs remained live with the screen owned by their ZX-UX process.
Both linked images fit the default 14,000-byte loader limit. The test asserts
unchanged bytes of all three original game inputs/outputs after execution.
No machine state, pixels, original listing, SSX, or framebuffer was modified.

Run from the repository root:

```sh
RBC_TWO_INKEY_CAPTURE_DIR="$PWD/experiments/hisoft-rbc-2026-10-22/captures-2026-10-28" \
python3 -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_scuba_swordsman_progression.py -v
```

| Original or emulator capture | Bytes | SHA-256 |
| --- | ---: | --- |
| Scuba BAS | 8,246 | `55f843260e3ead814cdae91e3e84590d35eea2740d6ed9cb49b9d628c626af74` |
| Scuba TZX | 8,731 | `26b31f55aa6219740e3d64fa7a3f1c49f36d035d30cd4f663daf8bdba31e3f92` |
| Scuba published SSX | 13,965 | `35218cc1def949320b3ed9d44e032f0dffd5c2a59dd9219d2203daf3ca937981` |
| `scuba-waiting.png` | 4,416 | `a93e37d4811f0d551e755efd75c71844ea33d77cab2b29001d472f1122de689a` |
| `scuba-progressed.png` | 2,645 | `7e1e9e403dc63f3a318997fe62e95ca272c4b64b4652d26d5ae0f90fad039825` |
| Swordsman BAS | 5,477 | `63dfccabffba9c2b5c042243a8232062fd3af13b88d98c08f5fdaa367af02434` |
| Swordsman TZX | 5,077 | `11219d7b2501f67088946bee52155bf641b8515445b0302c2980c7b95185d4e4` |
| Swordsman published SSX | 10,265 | `56772922a3ac7f90e367e22c5b70e3f3c19a101b5946c02b75f6e70cfca06d32` |
| `swordsman-waiting.png` | 3,287 | `c8db4471c0c91e402ead25fd1bb5240443098e947377d3390235f4a9bc61b8d6` |
| `swordsman-progressed.png` | 2,886 | `eca682fa0652567856c40ef25c10838a841b93126583e5f86fa31fdae582e615` |

The four PNGs came directly from the ZX-UX emulator framebuffer using
`rvm.write_png`, with no drawing, alteration or screen simulation.

The unchanged broad interaction gate still labels these two games as
`SCREEN UNCHANGED` under its older, mistimed scripts. These focused checks
resolve only the stated progression paths. Production INPUT, published
Flying Geese replay, and full 34-game gameplay remain open.
