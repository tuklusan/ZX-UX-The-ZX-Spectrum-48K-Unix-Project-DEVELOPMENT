# Native Flying Geese: 100-shot game-over screen

Authentic 48K ZX-UX Z80 framebuffer recorded on 28 October 2026, using
only the unchanged published SSX and keyboard presses in the real emulator.
No source file, linked bytes, screen pixels or machine state were edited.
This proves one complete shooting round and the displayed score, not all
possible gameplay outcomes or successful replay after the `INPUT` prompt.

Original source line 40 checks the key, line 60 ends the game after 100
shots, and lines 300-330 display the score and ask for the next game.
A controlled series of 130 `A` key presses produced the following genuine
screen at frame 4500 after launch:

- **SHOTS:101**, **SCORE 5**
- **GAME OVER**
- **SCORE:5 IN 100 SHOTS**
- **HIGHEST SCORE:5**

The final screenshot is `flying-geese-game-over.png`. The emulator still
owned the process screen; the game had not exited. An additional held
ENTER in a separate trial did not advance the `INPUT` replay prompt,
so replay is **not verified**. This is not proof that the original game
cannot replay with a corrected, source-verified INPUT implementation.

Reproduce from the repository root after building the unchanged ZX-UX
system tape and recovering the original 768-byte font:

```sh
RBC_GEESE_CAPTURE_DIR="$PWD/experiments/hisoft-rbc-2026-10-22/captures-2026-10-28" \
  python -B -m unittest discover \
    -s experiments/hisoft-rbc-2026-10-22/tests \
    -p test_native_flying_geese_round.py -v
sha256sum experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/flying-geese-game-over.png
```

SHA-256:

```text
BAS       94cda828f926c95cb1b74803c471d7a28c0c9091d4a93e3a22f52919efbe731a
TZX       a416c968ce4026622887d6adcd4f85d87c1d72319944ee243d52d2b512a75674
SSX       920fef840c85b84e290b2c3f1818017f79b0661a5751af91e75233675eafedb2
PNG       2bd166ca28e93422fcf3f1962aa951dfa2aae0230b882d783b12fc3de3b486f5
```
