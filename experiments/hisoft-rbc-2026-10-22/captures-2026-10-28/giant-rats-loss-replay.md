# Giant Rats: native losing run and replay (2026-10-29 UTC)

The unchanged published `35-giant-rats.ssx` ran in the genuine ZX-UX
48K loader and Z80 emulator. Real keyboard `a` advanced the first help
page, and `b` started the maze. With no movement, five lives elapsed;
the original program displayed `You scored 0 points.`,
`The high-score is 0`, and `PRESS ANY KEY TO PLAY AGAIN`.
A genuine `c` key restarted the maze in the same live native process.
The summary disappeared and the game drew a new arena.
This proves the losing path and replay. No victory, successful rescue,
all movement keys, STOP, or shell-return result is claimed.

Reproduce against the frozen system tape and checked font:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_GIANT_RATS_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
experiments/hisoft-rbc-2026-10-22/tests -p test_native_giant_rats_loss_replay.py -v
```

- Original BAS SHA-256: `7148a4d5207b732c8bacf75eadce2a72217d29da52b3b02c5f2f1cc3cac0b2a0`
- Original TZX SHA-256: `4077a97c7df0f2e3bc422fc0d9b27a1a4f8d876f986b2d2662d4b8c3cd8de16d`
- Published native SSX SHA-256: `990f090d6e95fda45fec50225e788bb5874e68c4c09dd09c50d4806423b00bed`
- Frozen ZX-UX tape SHA-256: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`
- `giant-rats-gameover.png` SHA-256: `fdec6a90df2d3da6aecfd7c2f8006fa5dd9dfc17bef22dd8bd09e7d96adae49c`
- `giant-rats-restarted.png` SHA-256: `890f1e574a3434f254f46aeb01f8adcf6c9c80a35862c8ab9ee1b03b70d02d6c`

The two PNG files are unedited output from the emulator framebuffer.
No BAS, TZX, SSX, ROM, kernel, or system tape bytes were changed.
