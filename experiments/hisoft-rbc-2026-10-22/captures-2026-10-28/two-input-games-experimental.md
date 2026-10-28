# Original Minelay and Space Traffic — test-only INPUT progression

The checked production HiSoft ROM EDITOR path still stops at its original
INPUT prompt. These experiments replace that call only in three-base-witnessed,
pre-link assembly, assembled with `ras` and linked with `rld`. No original BAS,
TZX, published SSX, kernel or ROM was changed. The experimental executables
remain under untracked `build/tmp/`. They are not production repairs.

Tested in the real ZX-UX 48K kernel/Z80 emulator:

- **Minelay:** Without input, the native program remains at `Press ENTER to
  start...`. With `ENTER`, another `ENTER`, difficulty `2`, then `Q`, it enters
  the original score/lives maze scene. The two final framebuffers differ.
- **Space Traffic:** Without input, the original instructions remain visible.
  With `ENTER`, another `ENTER`, the game starts and eventually displays its
  own `You scored 0 points.` / `PRESS ANY KEY TO PLAY AGAIN.` screen. This
  proves a real round progressed, not that directional/fire controls work.

These observations do **not** establish INPUT safety or full game play. ZX-UX
canonical `/dev/tty` truncates at 79 characters; the test-only editor has no
complete Sinclair editing equivalence or long-line refusal. The published
production INPUT compiler path and Flying Geese published replay are still
unrepaired/unverified. These experimental SSX images must not be installed in
any game's `bin/` folder.

To reproduce after restoring the checked frontend, compiler tape and RBC CLI:

```sh
export RBC_FRONTEND_DIR="$PWD/build/tmp/rbc-inputs/upstream-pyhsb"
export RBC_HISOFT_TAPE="$PWD/build/tmp/rbc-inputs/hisoft48.tap"
export RBC_TWO_INPUT_CAPTURE_DIR="$PWD/experiments/hisoft-rbc-2026-10-22/captures-2026-10-28"
python3 -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_input_two_game_progression.py -v
```

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Minelay BAS | 4,466 | `502737071cab6eb9bc74c48504e41fc4f41efcbdba57ea0b6c7368d1dcef9d7e` |
| Minelay TZX | 4,676 | `5e3a4d2338d405b0f8ccd71a5164cacab4688c58ac59185dfdfb138f1b50149c` |
| Minelay published SSX | 10,824 | `f35b03c09dfb4cc6dedae153e3e8f24250d1e9b75daed3fbde4a4a2b9900f341` |
| Minelay test-only SSX | 10,883 | `0f9def40134b95981997d437f4094ac494387b5908f4e4a8df31d4bea79ecdde` |
| Minelay waiting PNG | 5,329 | `45987a9685d524ced16aded87d0ba51f1796936d72d994254004c023c9bac170` |
| Minelay maze PNG | 4,474 | `14c9e2e814802965babbc522a9ed2a1c9c29e9543fd3fc388d7067b459874478` |
| Space Traffic BAS | 4,032 | `db45faadd47ec6d624d060eb2a9caf6744b97ae127511c7317d5b733223d8c10` |
| Space Traffic TZX | 4,564 | `c62f497db03d156bf7819600fde5c26e2977072c4678fd630a8e460799a94d45` |
| Space Traffic published SSX | 10,560 | `ca89a02115438e0feffc17bb564c2d0bab1dcf153d087593814289261efe4d6a` |
| Space Traffic test-only SSX | 10,619 | `b8e83fd9f15da2c5fbeb79c83a2b0ce92f42b54cadbe43fe30611e914852f4bc` |
| Space Traffic waiting PNG | 5,408 | `50ec21eeeb4e08f635c955bcc646c60b236a680d503fe7b64f32c82add050f20` |
| Space Traffic round-over PNG | 1,671 | `27d5b8f958cb49a54b95361e7204f6cee0cf2a13a1bba1993f305e9cf456b442` |

All four PNGs were written by `rvm.write_png` directly from the genuine
emulator framebuffer. They were not drawn or modified. The `-blocked.png`
filenames denote the awaiting-input state, not a kernel process crash.
