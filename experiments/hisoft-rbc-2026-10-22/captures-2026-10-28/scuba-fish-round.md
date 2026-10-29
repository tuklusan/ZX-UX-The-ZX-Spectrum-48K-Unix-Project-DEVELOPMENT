# Scuba: one real fish, air-loss score, and native STOP (2026-10-29 UTC)

The original published `14-scuba.ssx` ran unchanged under the real ZX-UX
48K loader and Z80 emulator. The source-guided keyboard route used actual
`X`, `S`, and `F` keys; it never set game coordinates, random values,
process memory, ROM, the screen, or native code directly.

Original BASIC line 365 adds one to `P` after a fish collision. The actual
Spectrum framebuffer showed `FISH CAUGHT = 1` and `AIR LEFT =   107`.
The diver then stayed underwater until the original air timer expired.
The display showed `1 FISH BROUGHT BACK FOR SUPPER`, `RAN OUT OF AIR...`,
and `ANOTHER GO???`. The original `N` answer executed `STOP` with exit
status zero; the process released the screen in the same kernel session.
The test does not claim a shark encounter, 20 fish, victory, all movement
combinations, or independently verify a shell prompt after STOP.

The automatic test is `tests/test_native_scuba_fish_round.py`. From repo
root, with the checked ZX-UX tape at `build/out/ZX-UX.tzx`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_SCUBA_FISH_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
  experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_scuba_fish_round.py -v
```

One real-emulator test passed. Seven Scuba source/ROM-support tests and six
ROM syntax tests also passed. The runner checks the original input and SSX
bytes again after play. The published SSX remains admitted under the
unchanged 14,000-byte limit: file **13,965**; image **12,310**; BSS **862**;
stack **384**; image+BSS+stack **13,556** bytes.

| Original file or capture | SHA-256 |
| --- | --- |
| `14-scuba.bas` | `55f843260e3ead814cdae91e3e84590d35eea2740d6ed9cb49b9d628c626af74` |
| `14-scuba.tzx` | `26b31f55aa6219740e3d64fa7a3f1c49f36d035d30cd4f663daf8bdba31e3f92` |
| `14-scuba.ssx` | `35218cc1def949320b3ed9d44e032f0dffd5c2a59dd9219d2203daf3ca937981` |
| `48.rom` | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| Frozen ZX-UX tape | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| `scuba-fish-caught.png` | `492f408be200e68f3a120bccb247b9be5a787f897afee84fd684b4746e272ea5` |
| `scuba-fish-air-loss.png` | `86feaed694c6389dfe1e2848c07bbd022875b0a4b0ecea1cb35fad0f003621d3` |

Both PNGs are genuine, unedited `rvm.write_png` captures from the original
ZX Spectrum framebuffer. An independent Y-replay probe reached the original
instructions, but its separately captured result is not part of this test.
This milestone proves one scored losing round and STOP, not exhaustive gameplay.
