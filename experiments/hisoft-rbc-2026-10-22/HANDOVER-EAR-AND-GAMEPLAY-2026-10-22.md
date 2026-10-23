> Historical checkpoint only. The test-only keyboard port override described
> below was retired after the ULA feedback fix at commit
> `b655d67e6a519d47ff2321dacba890e330a16e5c`.
> Follow `RBC-ULA-POSTFIX-2026-10-23.md` for current native tests and settings.
> The earlier workaround must not be restored.

# ZX-UX RBC — EAR input and native game checkpoint (2026-10-22)

Project: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT` (branch `main`). This note records the latest game tests before work continues in a different chat. For recovery, read GitHub `main` first; no local files from an older chat are guaranteed to exist. The last verified baseline for this note was commit `bcd9c986ef2b708a5462b518e0bf6e7d12517062`, tree `6f44d68f09b9752270d591c47ad83e1345d93fbd`.

## Technical finding: why the EAR input affects keys

The original, **unchanged** Galaxians BASIC reads the entire ZX Spectrum keyboard I/O byte in line 140 (`IN 65278`) to test `x` and `z`, and line 155 (`IN 32766`) to test `m`. It directly compares that byte to numeric constants without masking off non-keyboard bits. Keyboard and cassette EAR input share the low-address-selected even I/O read: bits 0-4 represent keys, while bit 6 is the EAR signal. The observed emulator read during the test was `187` (`0xBB`) with `x` held instead of the BASIC source's expected `251` (`0xFB`): **exactly bit 6 (`0x40`) differs**. Idle reads also differed by `0x40` (`191` versus `255`). Therefore, the game's full-byte comparisons ignored correctly pressed keys.

For an isolated test only, `stage/keyboard_ula.py` patches the runner's `machine.cpu.read_port` so an even port read ORs bit 6 when `machine.pulses is None`. Normal cassette-pulse handling remains delegated to the emulator. The hook is applied *after* system boot by `stage/gameplay_ports.py` and `stage/frame_probe.py`. **This is not a production ZX-UX SDK/kernel/emulator fix.** A real 48K ULA's no-tape EAR value must be verified in context, including the port output/MIC/speaker state and tape activity; simply forcing bit 6 high in the shipped emulator is not yet justified. Keep this experimental workaround clearly labeled until genuine behavior is validated.

## Verified or observed work

- GitHub Actions run `39894329893` succeeded across five shards. Full compilation results remain **16 of 121 inputs**, not 121 passes. The 60 original BASIC tapes were scanned with **44 safe `PAUSE 0` replacements in 25 programs**. Host Python tests: **34 passed**. All original `.bas` and `.tzx` game sources were left unchanged.
- Galaxians compiles into native SSX1, boots, starts with SPACE, and its ship moves left on `z` and right on `x` **under the test-only EAR adjustment**. The GitHub checkpoint includes actual native frames and movement reports.
- Exploratory `m`-held versus no-fire local test reported a vertical laser trace of **134 versus 11 pixels**, **11 versus 0 full-laser frames**, and **40 versus 0 points gained**. These are **isolated patched-test results**, not a complete gameplay pass. The accompanying five genuine emulator screenshots and exploratory Python probes are archived in `RBC-CONTROLS-CAPTURES-2026-10-22.zip`; the scripts contain temporary absolute paths and must be adapted before reuse. A clean reproducible scoring/laser CI test is still required.
- Invaders native frame comparison aligned **48 of 49 enemy sprite cells** at selected frame 249. Its actual PNG and alignment data are already permanently stored under `results/`. Visual colors, text, remaining sprites, timing, input, and gameplay are not fully verified.
- `rbc-native-controls-checkpoint-2026-10-22.zip` already contains compiler sources, binaries, reports, and native screenshots. `RBC-CI-2026-10-22.md` records confirmed runner results.

## On return: exact next work

1. Read live remote `main`, this addendum, `RBC-CI-2026-10-22.md`, and the newly obtained ZX-UX feedback. Preserve the existing full private checker and the entire case-insensitive restricted list without changes.
2. Reproduce or analyze actual ULA input semantics with no tape, tape playback, MIC/speaker port writes, and scan states. Check the kernel, ROM, and emulator interactions. Decide whether the production emulator needs a bit-6 correction; do not promote the runner-only hook without confirmation.
3. With a faithfully modeled port, recompile both unmodified game sources, rerun physical press/hold/release/no-key tests, and compare native screenshots with authentic original screenshots. Turn the laser/scoring observations into a repeatable native regression test.
4. Continue compiler conformance batches from the same **16/121** measured baseline; retain strict memory safety and run all five shards after fixes. Never call compilation, boot, a changed frame, or sprite alignment a full gameplay pass.
5. Run the full private checker before pushes; commit and fast-forward push useful source, tests, captures and reports to GitHub. Verify the **remote commit, tree and blob SHAs**. Nothing necessary should live only in temporary storage.

## Permanent recovery paths

- `experiments/hisoft-rbc-2026-10-22/HANDOVER-RBC-2026-10-22.md` — original complete handover
- `experiments/hisoft-rbc-2026-10-22/RBC-STATUS-2026-10-22-2.md` — movement and native control status
- `experiments/hisoft-rbc-2026-10-22/RBC-CI-2026-10-22.md` — five-shard success and Invaders alignment
- `experiments/hisoft-rbc-2026-10-22/rbc-native-controls-checkpoint-2026-10-22.zip` — full preserved compiler/build/results checkpoint
- `experiments/hisoft-rbc-2026-10-22/stage/keyboard_ula.py` — **test-only** EAR hook
- `experiments/hisoft-rbc-2026-10-22/RBC-CONTROLS-CAPTURES-2026-10-22.zip` — supplementary fire frames and exploratory scripts

**Status**: Saved as a development checkpoint, not a release. Await separate ZX-UX feedback before choosing the permanent ULA treatment.
