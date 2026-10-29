# Galaxians: real native loss and replay (2026-10-29 UTC)

The original published `25-galaxians.ssx` ran unchanged in the ZX-UX 48K
Z80 emulator with the matching frozen system tape, ROM, and original BASIC.
No source, program bytes, loader, or framebuffer pixels were altered.

The real keyboard accepted `a` at the original start screen.
Without further action, the game reached original BASIC line 4050 and showed
`G A M E  O V E R` at row 10 and `PRESS ANY KEY TO PLAY AGAIN` at row 18.
A second real `a` key cleared the game-over screen and began a fresh fleet;
`HIGH-SCORE:` was visible and neither game-over message remained.
The same live native process kept screen ownership. The game did not exit.

This is a complete losing round and restart. It does **not** prove winning,
all fleets, scoring accuracy, or every key. The test samples actual
Spectrum framebuffers, decodes the checked text using the original ROM font,
and captures unmodified PNGs using `rvm.write_png`.

| Source or capture | SHA-256 |
| --- | --- |
| Original BAS | `5058e12f1f4b95871158e9d1c30785c15d5afc24930f1cb28520f654feacd4e3` |
| Original TZX | `35c9bf46184d62de7abd06eaeb7e73ccb289e5f451122406bda75d6bde19bc35` |
| Published SSX | `50d839dc031fcbf4ff8d575f181033f16277c8cb26b7114ccdc5e4489c7695fc` |
| Frozen and rebuilt ZX-UX TZX | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| Original 48K ROM | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| `galaxians-gameover.png` | `258cda0196bbe5e693e65792d3eb9da9e65a2ece207d21655a9678092c7b2dc6` |
| `galaxians-restarted.png` | `6e579a705833a9b125cbc6944d83894822222f1074c2f72bd1e805c4f179844d` |

With the checked `build/out/ZX-UX.tzx`, matching `kernel.json`, and recovered
`build/tmp/rbc-recovered/rbc/font32.bin`, reproduce from the repository root:

```sh
RBC_GALAXIANS_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_galaxians_gameover_replay.py -v
```

One passing real-emulator test verifies this losing round and replay. All-game
full-play testing remains open; prior screen-response tests are separate.
