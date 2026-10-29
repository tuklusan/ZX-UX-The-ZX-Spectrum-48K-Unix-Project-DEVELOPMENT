# Space Traffic: original five-life loss and replay (2026-10-29 UTC)

The unchanged published `30-space-traffic.ssx` ran in the real ZX-UX 48K
loader and Z80 emulator. Two real ENTER keys dismissed the original INPUT
opening. With no movement or fire, the native game reached its original
BASIC lines 4130-4170 after five lives. The framebuffer displayed
`You scored 0 points.`, `The high-score is 0.`, and
`PRESS ANY KEY TO PLAY AGAIN.`.

A real `a` key then dismissed the end-of-game prompt. The same native process
kept screen ownership, the old score message disappeared, and the new game
screen continued changing over another 120 frames. No BASIC, TZX, SSX,
ROM, kernel, machine RAM, randomness, or screen pixels were modified.

This verifies one complete losing round and an active restart. It does not
prove satellite collection, successful survival, every movement key, scoring
accuracy outside the zero-score case, victory, or shell return.

Reproduce from the repository root with the checked original ROM,
`build/out/ZX-UX.tzx` byte-identical to `dist/zx-ux/tzx/ZX-UX.tzx`,
matching `kernel.json`, and the checked 768-byte `font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_SPACE_TRAFFIC_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_space_traffic_loss_replay.py -v
```

The real-emulator test passed. The six strict ROM syntax tests passed. An
additional INPUT isolation test could not run because the external original
HiSoft compiler was absent; no success is claimed for that skipped test.
The original source, tape, linked program and ROM bytes are checked again
after execution. The unchanged default loader limit is 14,000 bytes.

| Checked file or capture | Bytes | SHA-256 |
| --- | ---: | --- |
| Original BAS | 4032 | `db45faadd47ec6d624d060eb2a9caf6744b97ae127511c7317d5b733223d8c10` |
| Original TZX | 4564 | `c62f497db03d156bf7819600fde5c26e2977072c4678fd630a8e460799a94d45` |
| Published SSX | 10941 | `5c7153706186ca60a5d12f47f1259ece8e19d9c32e3bb90a1e12e87a038f77e7` |
| 48K ROM | 16384 | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| Frozen ZX-UX tape | 29742 | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| `space-traffic-gameover.png` | 1671 | `27d5b8f958cb49a54b95361e7204f6cee0cf2a13a1bba1993f305e9cf456b442` |
| `space-traffic-replayed.png` | 2015 | `5eefbbe169fe73147b2241e8ad26daa7d4bc0de5172e8ad25c8afe5b0c85cd9c` |

Loader admission: file **10,941**; image **9,716**; BSS **900**;
stack **384**; total image+BSS+stack **11,000** bytes. Both PNGs are
genuine `rvm.write_png` framebuffer captures, with no image editing.

A separate concurrent ten-game investigation was inconclusive for other
games; neither screen changes nor incomplete/expired runs have been counted
as complete gameplay proof.
