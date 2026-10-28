# Original Flying Geese: test-only INPUT replay

The published native Flying Geese SSX stays untouched. Its original ROM EDITOR
INPUT path does not leave the GAME OVER screen after ENTER in the bounded 4,800-frame
real-kernel probe. No production RBC repair is claimed.

A separate experimental SSX was assembled and linked from the original,
three-base-verified pre-link HiSoft source with one source-owned INPUT editor
substitution. This candidate receives ENTER after 100 shots, clears GAME OVER,
and starts a new Flying Geese board in the real ZX-UX loader. This **does not**
approve the experimental INPUT bridge for release: editing limits and all
keyboard, numeric-input, error and memory-safety cases remain incomplete.

Reproduce from the repository root with the checked HiSoft frontend/tape,
rebuilt ZX-UX system tape and original 48K ROM. Set `RBC_FRONTEND_DIR`
and `RBC_HISOFT_TAPE` to the checked compiler inputs, then run:

```sh
python3 -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
    -p test_native_flying_geese_replay_candidate.py -v
```

Observed with the unchanged original ZX-UX system tape:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Original BAS | 2,858 | `94cda828f926c95cb1b74803c471d7a28c0c9091d4a93e3a22f52919efbe731a` |
| Original TZX | 2,989 | `a416c968ce4026622887d6adcd4f85d87c1d72319944ee243d52d2b512a75674` |
| Published SSX | 8,526 | `920fef840c85b84e290b2c3f1818017f79b0661a5751af91e75233675eafedb2` |
| Test-only INPUT SSX | 8,585 | `0730de046ed07ad0b6f1a7397ec499c1af48040da099c3cfbe15e2ce2ede3fb9` |
| Candidate GAME OVER PNG | 3,836 | `0ec8db12bee7ee1a7fbf2ed80d60e976d582d88803054b769364d7c809c553ca` |
| Candidate after ENTER PNG | 2,821 | `162d72f2d0d08af92a0410add49c8b6341f39b8c8cacaa22361d6b3c4da5c1eb` |

Both PNGs come from genuine ZX-UX/Z80 framebuffer capture. The test verifies
that all three original game input/output files have exactly the same bytes
before and after the experimental run. The experimental SSX stays untracked
under `build/tmp/` and is not published in a game's `bin/` directory.
