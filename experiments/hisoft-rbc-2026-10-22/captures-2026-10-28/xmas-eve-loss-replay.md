# Xmas Eve: native loss and replay (2026-10-29 UTC)

The unchanged published `37-xmas-eve.ssx` ran under the real ZX-UX 48K
loader/Z80 emulator. Two actual keyboard keys advanced through the original
instruction screens. With no gifts delivered, the program reached its
original BASIC game-over (lines 6000–6050) and displayed
`G A M E  O V E R`, `PRESS ANY KEY TO PLAY AGAIN`, and `PRESENTS:0`.
A third key started a new round, removing the game-over prompt while the
same process kept screen ownership. This proves a losing round and replay,
not gift delivery, successful scoring, all controls or full gameplay.

Reproduce with the unchanged frozen system tape in `build/out/ZX-UX.tzx`,
the matching `build/out/kernel.json`, and the checked 768-byte font in
`build/tmp/rbc-recovered/rbc/font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_XMAS_EVE_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
experiments/hisoft-rbc-2026-10-22/tests -p test_native_xmas_eve_loss_replay.py -v
```

Original BAS SHA-256: `4b2f528dad7b7837a0a54ebfae60a3a84c3e2a735ac84832b87b17e8469c5d84`.
Original TZX SHA-256: `143480896390e320e2e8f2e5414e20b141b175daafd69cc5babbf27c9122feca`.
Published SSX SHA-256: `e1e57632a0e57f1529b4a8c9d5743c31d9bbb55d0d50ec52c66c388296af7104`.
Frozen tape SHA-256: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`.

Genuine ZX-UX framebuffer captures, without edited pixels (`rvm.write_png`):

- `xmas-eve-gameover.png`: SHA-256 `293016a9ad4d0e09e197f6194b8f4ff5b8508bc32ca4e4a4b6a643b52b472ea6`.
- `xmas-eve-restarted.png`: SHA-256 `a42c2aae5fbd05fe319465377082f225d2978f5698aa13d7cf5f2f9000a03738`.

All 120 BAS/TZX originals and published SSX bins remain untouched by this test.
