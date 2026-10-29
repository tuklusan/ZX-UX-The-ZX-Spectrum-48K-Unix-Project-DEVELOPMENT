# Dam Eaters: native dam breach and replay (2026-10-29 UTC)

The unchanged published `31-dam-eaters.ssx` ran in the actual ZX-UX 48K
loader/Z80 emulator. A keyboard `A` started the original game. Without
using the three cannons, the dam was breached. The program displayed
`You Scored 0 Points.`, `The High-Score Is 0`, and
`PRESS A KEY TO PLAY AGAIN` (original BASIC lines 4055–4090).
A keyboard `B` cleared the end-of-round message and resumed the game,
showing the fresh `Score:0` field. The same native process kept the screen.
This proves a losing round and successful restart, not a win, cannon accuracy,
full gameplay, or shell return.

Reproduce with the frozen system tape at `build/out/ZX-UX.tzx`, matching
`build/out/kernel.json`, and the checked 768-byte font at
`build/tmp/rbc-recovered/rbc/font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_DAM_EATERS_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
experiments/hisoft-rbc-2026-10-22/tests -p test_native_dam_eaters_loss_replay.py -v
```

Original BAS SHA-256: `e9a08740f628124537b979eb0a4d08118943ac2b1ca85f167af459b418f34ab4`.
Original TZX SHA-256: `2fd05fb6fcb0ef5066b5b5800f9492a87339fc9383cd7cc14c0ba87d4e0b0fc6`.
Published SSX SHA-256: `daf195da53fa1af39821852c993551c161bfcea1db2d1ca120661b7482faeb7f`.
Frozen tape SHA-256: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`.

Genuine, unedited emulator framebuffer captures (`rvm.write_png`):

- `dam-eaters-breached.png`: SHA-256 `f9c3ad4ab452f1401fe5feb4bc6fb518a32fa512910554a314ae70bd6078583d`.
- `dam-eaters-restarted.png`: SHA-256 `654cd1628489a88130e38ce6c23bef50e1e73acab835f247816839181b3f34e7`.

All BAS, TZX, SSX, ROM, kernel, and other game bytes remain unchanged.
