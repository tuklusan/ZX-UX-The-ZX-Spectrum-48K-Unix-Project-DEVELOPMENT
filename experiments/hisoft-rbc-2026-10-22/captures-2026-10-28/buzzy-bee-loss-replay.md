# Buzzy Bee: native collision, survival score and restart (2026-10-29 UTC)

The unchanged published `32-buzzy-bee.ssx` ran in the actual ZX-UX
48K loader and Z80 emulator. At the instructions, real keyboard `a`
started the game. With no movement, a descending flower eventually met
the bee. The original game showed `You survived for 3 seconds.`, a
high-time message, and `Press any key to play again.`. Pressing `b`
restarted the game, removed the score screen, and redrew the garden.
This proves a natural losing round and replay, not a win, all controls,
STOP, or shell return. The test accepts any nonnegative displayed
survival time rather than assuming a fixed clock outcome.

Reproduce with the frozen ZX-UX release tape and checked font:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_BUZZY_BEE_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
experiments/hisoft-rbc-2026-10-22/tests -p test_native_buzzy_bee_loss_replay.py -v
```

- Original BAS SHA-256: `edaccced90c09791d578c7a56f9a9e5004ec9d9198aa9ee8072ede30318a64b3`
- Original TZX SHA-256: `ca11a8363bcf6373ed1dcd0fcfd83bde3fd753a4f50e666e3d568c1a8a6704ed`
- Published native SSX SHA-256: `78b5d5eaf801a49199bf8eb5925740b21294c5ee867d78b7806ea14208c4d3be`
- Frozen ZX-UX tape SHA-256: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`
- `buzzy-bee-gameover.png` SHA-256: `1d7d3055d6e841f7559ad46e1cfdebb43ace2a00a69ff68802ad6ce0424e9eb1`
- `buzzy-bee-restarted.png` SHA-256: `b4e7391581d60051bc4e225083722e3a2e9056e0976107e57fa51928b0ba64a1`

Both PNG files were captured directly from the native emulator framebuffer.
No published program, original BASIC/TZX, ROM, kernel or tape was edited.
