# Bricklayer: original wall reaches game-over (2026-10-29 UTC)

The unchanged published `42-bricklayer.ssx` was loaded through the real
ZX-UX 48K kernel and executed on its Z80 emulator. A real `a` key released
the original instruction-screen PAUSE. No bombs or humanoids were dropped.
The moving wall advanced until the game displayed `ANOTHER GAME?` in its
original BASIC end-of-round path (lines 125 and 1000–1040).

The genuine frame showed `SCORE:0`, `HI:0`, and `LIVES:10`. Ten lives still
remaining distinguish this game-over from the original zero-lives branch.
The native process was still running and owned the screen at the prompt.
This proves one complete wall-build losing round, not the bomb/humanoid
strategy, INPUT replay, a game victory, or STOP and shell return. A
separate attempted `n` answer did not establish an exit, so replay and
exiting from this published game remain unverified.

Reproduce from repo root with the checked `build/out/ZX-UX.tzx` and native
`font32.bin` available at the existing build paths:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_BRICKLAYER_WALL_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
  experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_bricklayer_wall_gameover.py -v
```

The test passed. The existing `test_native_bricklayer_gameplay.py` keyboard
comparison also passed. Native loader admission: file **6,667** bytes;
image **6,049**; BSS **366**; stack **384**; image+BSS+stack **6,799**,
under the unchanged 14,000-byte limit. All three game files are checked
before and after the test, with no edits to original game or kernel.

| Original file or capture | SHA-256 |
| --- | --- |
| `42-bricklayer.bas` | `79d2236096c2460d7060db26a61792f998e0231b5675da415dd4088dea7e9e99` |
| `42-bricklayer.tzx` | `08c6679392614d0b7b26af63f905f8dc4173a93004bf0d0ec073dc70abf4bdff` |
| `42-bricklayer.ssx` | `2da076ca4c4d209c66745fd0cbac4164c35598de23cafa06eeca8e6579528170` |
| Frozen ZX-UX tape | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| `bricklayer-wall-gameover.png` | `84b33a09c0d53e8aea33fd2df54e3cd767ed6c300b9a8e865e8de6fc311be12f` |

The PNG is an unedited `rvm.write_png` image from the genuine 6,912-byte
Spectrum framebuffer. No screenshot or gameplay result was constructed.
