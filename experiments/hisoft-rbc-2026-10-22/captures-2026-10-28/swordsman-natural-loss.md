# Native Swordsman: combat to natural loss

The unchanged published `54-swordsman.ssx` ran through the original ZX-UX
loader and real 48K Z80 emulator. Without keyboard input, the program reached
its first fight by frame 200, displayed `TOTAL POINTS=1` and the original
`GANGRENE GOAT` opponent, and reached the game's loss screen by frame 500.
The loss screen said `ANOTHER HERO BITES THE DUST`, reported zero monsters
killed and one point, and offered the original Y/N replay menu.

These observations prove visible native game progression and natural defeat,
not a player-controlled victory, replay, an N-key exit, or complete gameplay.
The broader 34-game keyboard gate still lists Swordsman as an unverified input
effect. No INPUT repair is implied.

Reproduce from the repository root after rebuilding the checked ZX-UX tape
and recovering the checked original font:

```sh
RBC_SWORDSMAN_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
    -p test_native_swordsman_natural_loss.py -v
```

All captures are the unedited genuine 6912-byte Spectrum framebuffer rendered
by `rvm.write_png`. The test enforces SSX loader size, running-process screen
ownership, real rendered text, source preservation and frozen kernel identity.

| Original input or output | Bytes | SHA-256 |
| --- | ---: | --- |
| `54-swordsman.bas` | 5,477 | `63dfccabffba9c2b5c042243a8232062fd3af13b88d98c08f5fdaa367af02434` |
| `54-swordsman.tzx` | 5,077 | `11219d7b2501f67088946bee52155bf641b8515445b0302c2980c7b95185d4e4` |
| `54-swordsman.ssx` | 10,265 | `56772922a3ac7f90e367e22c5b70e3f3c19a101b5946c02b75f6e70cfca06d32` |
| `swordsman-combat.png` | 2,955 | `ea6ee187ed51798885e221f4ad5003eefe505e8c88a4e39e77654c56a3f905b7` |
| `swordsman-defeat.png` | 3,287 | `c8db4471c0c91e402ead25fd1bb5240443098e947377d3390235f4a9bc61b8d6` |

The published SSX has 9,195 image bytes, 1,488 BSS bytes and a 384-byte
stack: 11,067 bytes total, below the 14,000-byte loader limit.
