# Genuine native RBC screen captures — 2026-10-28

These PNGs came from a running ZX-UX 48K Z80 virtual machine or a real Xvfb/xterm terminal session. No pixels were drawn or edited after capture. The screenshots are examples, not proof of complete gameplay.

The compiler uses the checked HiSoft frontend and original ROM input, emits pre-link source, assembles with `ras` and links with `rld`. No optimizer or C48 game backend was used.

Run `sh REPRODUCE.sh` from this directory after rebuilding the checked compiler at `build/tmp/rbc-recovered/rbc` and supplying the checked frontend and compiler tape at the paths in the script. The generated SSX is compared byte-for-byte to the published Bricklayer SSX.

System tape SHA-256: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`. Its bytes match the frozen release build as checked during the runtime probe.
48K ROM SHA-256: `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42`.

| Program and captured view | Original BAS SHA-256 | Published native SSX SHA-256 | PNG SHA-256 |
| --- | --- | --- | --- |
| 42-bricklayer — `bricklayer-start.png` | `79d2236096c2460d7060db26a61792f998e0231b5675da415dd4088dea7e9e99` | `2da076ca4c4d209c66745fd0cbac4164c35598de23cafa06eeca8e6579528170` | `aa9a9ee5102314b6a21a88ab76e74e24429814ff798a51032d46413426ff6944` |
| 56-roots — `roots-start.png` | `f215e95bda4a945f105d008e2986cfde2d69334a23bb87511de1f3a594ae392a` | `15aa401e543850be8568652feaa0ea6024d3059ffa67288c9752b198672b355e` | `248a1a4c548c0dd22f14b1c89d2f2ab58f29d77e3e1decf30d5889bb6f8f5093` |
| 16-snap — `snap-start.png` | `bafb27e17cbeb2d437dfa0b00227a5af42a06b2dd80ba335779a5bb4d0545e5e` | `3d75bccf2e596364102724ca4bf93eae2dabf39556c8fe09eb6ed72108a2c702` | `ff308e70b8f471cd5de48264fbf6cc620b67c511bac3c01d106aed33aa1376f4` |
| 42-bricklayer — `bricklayer-after-break.png` | `79d2236096c2460d7060db26a61792f998e0231b5675da415dd4088dea7e9e99` | `2da076ca4c4d209c66745fd0cbac4164c35598de23cafa06eeca8e6579528170` | `d03a1974d2e0a8719f03b570efda935f153c59d4d634c4d7b62c117753c99bbe` |

The `snap-start.png` capture shows the original game screen with illustrated objects. The `bricklayer-after-break.png` capture was taken with `--final` after a genuine keyboard BREAK. The virtual machine reported `killed (BREAK)` and released screen ownership; a restored interactive shell prompt was not verified. Do not treat BREAK as proof of STOP or normal completion.

The terminal screenshot `native-cli-live-terminal.png` is a direct `scrot` capture of a live `xterm` running the verified native CLI under Xvfb. PNG SHA-256: `c3e9614c815925b0e520e9cc08e86437c2b0ed8d21a03f30a2a2e3b7fb1f708c`. The generated SSX SHA-256 matched the published Bricklayer image: `2da076ca4c4d209c66745fd0cbac4164c35598de23cafa06eeca8e6579528170`.

A separate two-line BASIC `STOP` test source was attempted and blocked by an unresolved relocation. These captures do not claim that native STOP, handled errors, shell return or complete game play have passed.

The independent 60 BAS and 60 TZX default-limit builds produced 34 equal runnable pairs and 26 documented failures. Each of the 34 published SSX files passed loader startup (150 emulated frames after launch); no broader game-play claim is made.


## Bounded real-keyboard gameplay check

The unchanged published `42-bricklayer.ssx` was started under the genuine
ZX-UX 48K loader for 750 frames after launch. Input scripts used the emulator's
real keyboard queue. The opening screen was dismissed, then the native program
advanced into a visible score/lives and wall scene. At identical frame counts,
`Z` (bomb) and `M` (humanoid) made different game-screen changes; an irrelevant
`X` matched the no-action control. The check ran in
`tests/test_native_bricklayer_gameplay.py`. These tests do not prove a complete
level or final gameplay victory.

| Genuine framebuffer | Input after opening | PNG SHA-256 |
| --- | --- | --- |
| `bricklayer-gameplay-z.png` | `a{WAIT 120}z{WAIT 200}z` | `f7356355368e1c103d2e7f42e29685f275e3ef7b72ad633d1b79cdbdfeabe41a` |
| `bricklayer-gameplay-m.png` | `a{WAIT 120}z{WAIT 200}m` | `e17b504caa90ff955746a08b56e3dbe1aa756d123dc60a9360f801c0cb3c89b1` |

The real native no-DATA-section `STOP` test additionally exercised three-base
source relocation, `GO SUB`/`RETURN`, zero-status STOP, physical screen release,
the working shell prompt, and a second successful native process in the same
kernel session. Natural completion was tested separately. Zero-BSS, one-past-end
relocations remain refused, not silently admitted.

The complete ROM-backed LLIST parity test passed all 6,581 original TZX BASIC
lines, with 28 passing tests in the `test_zx_tzx2bas.py` suite. This is a
ROM text-fidelity check, not a guarantee that every game has been played.
