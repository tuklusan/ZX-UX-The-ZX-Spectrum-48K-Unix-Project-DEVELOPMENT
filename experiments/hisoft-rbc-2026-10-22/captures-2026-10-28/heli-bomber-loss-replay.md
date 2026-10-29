# Heli-Bomber: native loss and restart (2026-10-29 UTC)

The unchanged published `33-heli-bomber.ssx` ran in the real ZX-UX 48K
loader/Z80 emulator. The original opening text was displayed. A genuine
keyboard `A` started play. No shots were fired; a bomb or city/tower loss
ended the round under the game's original BASIC code, showing `END OF GAME`,
`Your score was 0`, `High score 0`, and `Press any key to restart`.
A genuine `B` key restarted play; the loss prompt disappeared and the
in-game `+` crosshair appeared. The process retained screen ownership.
These observations prove one losing round and restart, not a win, all levels,
all shooting controls, full gameplay coverage, or shell return.

Run this existing-source test from repository root on a configured ZX-UX host:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_HELI_BOMBER_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
experiments/hisoft-rbc-2026-10-22/tests -p test_native_heli_bomber_loss_replay.py -v
```

Requires the frozen system tape copied unchanged to `build/out/ZX-UX.tzx`,
its matching `kernel.json`, and the checked 768-byte `font32.bin` at
`build/tmp/rbc-recovered/rbc/font32.bin`. The test checks the system tape
against the frozen release; it never rebuilds or edits any game file.

SHA-256 of original BAS: `6ee21044d22e51af15e71916d9973ac50d75c36ee9ee10cc71a3b222fcf1cdf0`.
SHA-256 of original TZX: `f882b8614acf6864d81813f804cb25b21d818f33564f69c2b98756b26f276eeb`.
SHA-256 of published SSX: `5372d61a77e793f80fe9fcb4de01ce3cd238bd1560e94a8c27ff8fe9dcf0e4b4`.
SHA-256 of frozen system tape: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`.

Real framebuffer PNGs, written without pixel edits by `rvm.write_png`:

- `heli-bomber-gameover.png`: SHA-256 `46e9f895c132424cf4ba2718b9fd947914025f8f3ac99f4b1f3f05770b385d33`.
- `heli-bomber-restarted.png`: SHA-256 `4907909f67b452df922032cf9bf27009e22003596e055dfc34bc3639d0b8493f`.

The earlier 34-game paired-screen test still covers screen response only.
