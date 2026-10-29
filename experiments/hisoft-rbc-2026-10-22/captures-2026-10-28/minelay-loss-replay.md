# Minelay: original native maze loss and easier-game replay (2026-10-29 UTC)

The unchanged published `01-minelay.ssx` ran under the genuine ZX-UX 48K
kernel and Z80 emulator. The source-guided keyboard script advanced the
opening and chose the easier game. Without any further movement the game's
original BASIC exhausted its three lives and reached the game-over prompt
(lines 6007-6045). The genuine framebuffer displayed `G A M E  O V E R`,
`You scored 0`, `The high-score is 0`, and the original choice of difficulty.

The real keyboard then pressed `2`. The same native process drew a fresh
maze with `Score 0` and `Hi-score 0`. The old game-over text disappeared,
and the process retained screen ownership. This proves a natural losing
round and successful easier-game replay, not an egg collected, winning,
all movement controls, mine damage, or shell return.

The test asserts the original BAS, TZX, linked SSX and ROM are unchanged
before and after the actual emulator run. No process memory, random source,
original game text, binary, kernel, or screenshot pixels were patched.

From repository root with the frozen ZX-UX tape in `build/out/ZX-UX.tzx`,
its matching `kernel.json`, and the checked 768-byte `font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_MINELAY_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_minelay_loss_replay.py -v
```

The real-kernel test passed. Six strict ROM syntax tests also passed.
A separate INPUT isolation test was skipped because its external HiSoft
compiler input was absent; it is not counted as a pass.

| Original or captured bytes | Bytes | SHA-256 |
| --- | ---: | --- |
| Original BAS | 4466 | `502737071cab6eb9bc74c48504e41fc4f41efcbdba57ea0b6c7368d1dcef9d7e` |
| Original TZX | 4676 | `5e3a4d2338d405b0f8ccd71a5164cacab4688c58ac59185dfdfb138f1b50149c` |
| Published native SSX | 11205 | `4f574b5eaa66e1c3fb10f7418f1c05b97428043fff2971782137ab4b7413844f` |
| Original ROM | 16384 | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| Frozen system tape | 29742 | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| `minelay-gameover.png` | 1904 | `b6f1981d2f3a2738a4a6a36876bbd077346fd6727ac442fb35ec1a97aa4a020d` |
| `minelay-replayed.png` | 4020 | `cbc1d44554bea17d54599f7ae6ac2bdf008160fbe4eb3868fdbbdd2e0c5c45d1` |

Default loader admission: file **11,205**, image **9,904**, BSS **381**,
stack **384**, image+BSS+stack **10,669** bytes, below **14,000**. PNGs
were captured directly from the real 6,912-byte ZX Spectrum framebuffer
using `rvm.write_png`, without editing image pixels.
