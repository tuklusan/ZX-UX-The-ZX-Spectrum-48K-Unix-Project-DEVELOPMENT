# Flying Bomb: native miss and automatic new flight (2026-10-29 UTC)

The original, published `12-flying-bomb.ssx` ran under the real ZX-UX
48K loader and Z80. Without keyboard input, its aircraft passed the target
and displayed `LOST!` (original BASIC line 810). The display still showed
`SCORE:0`, with target distance negative. Original BASIC lines 900–920
then restarted the next flight automatically. Its target distance became
positive, the `LOST!` message disappeared, and the same live process kept
screen ownership. This proves one losing flight and automatic retry, not a
successful bombing run, all controls, complete game, or shell return.

Reproduce on a host with the unchanged frozen tape and matching kernel.json
in `build/out`, and the checked 768-byte font in
`build/tmp/rbc-recovered/rbc/font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_FLYING_BOMB_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
experiments/hisoft-rbc-2026-10-22/tests -p test_native_flying_bomb_loss_restart.py -v
```

SHA-256 BAS: `7501911856ac8b01521d91bc2b2762b784e2faa719758956c55e5588444932c9`.
SHA-256 TZX: `a1ababc76ab5162657216f3b0ec7ec810ac8f70bca2adc9c68e387461df55f9e`.
SHA-256 SSX: `3815ca1dbb726105017811ae18074527dee0e5fe4c7b7fb755590cb5d0816a0b`.
SHA-256 frozen tape: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`.

Unedited genuine emulator framebuffer captures (`rvm.write_png`):

- `flying-bomb-lost.png`: SHA-256 `ead8d62b39e75106320715faa7ac8c2aeb69a9c3504dfd1d7e3c9394d089afef`.
- `flying-bomb-new-flight.png`: SHA-256 `a4aa1724d73503f6e9f7dd10ca256ee8546541c476a018ed5343aff5abe500ef`.

The original BAS, TZX, SSX, system tape, ROM, and other games were not edited.
