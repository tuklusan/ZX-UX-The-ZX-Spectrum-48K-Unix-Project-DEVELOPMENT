# BASIC-to-C48 workflow — v0.8

Applies to all 60 numbered Spectrum BASIC programs, in directory order 01–60.
Translate the real historical program, not a substitute. Continue autonomously
within the active session, without approval pauses between stages or programs.
No routine chat narration; report only a minimal final outcome or blocker.
No work continues outside an active session.

**Hard boundary:** ZX-UX `beta-0.2.0` is frozen. Write only inside
`src/bonus/60-programs/`. Preserve every original `BASIC/` file byte-for-byte.
Never modify the SDK, compiler, emulator, root scripts, `dist/`, or frozen
checks. Run frozen tools only with output in this workspace or isolated
disposable copies. GitHub `main` is permanent storage.

## Mandatory cross-chat recovery — do this FIRST

1. Read live DEVELOPMENT `main` HEAD, `PORTING-PROGRESS.json`, and this
   workflow from that same commit; reconcile any checkout before building.
2. Run `python build/port_progress.py status` on the current tree.
   As of the ROM BASIC gate reset, both completed arrays start empty and
   `next_program` is `01-minelay`. Prior 01/25/58 deliveries remain usable
   source, but are NOT accepted under the reset. No pilot bypasses survive.
3. Verify each new accepted port has new-policy checks, native SSX/TZX,
   genuine gameplay comparison and published results. Existing PASS reports
   from before the reset cannot themselves grant completion.
4. Continue only `next_program` in 01–60 order. Recheck previously ported
   source instead of discarding it. Keep `completed` as the accepted prefix;
   keep `pilot_completed` empty. Never advance for unfinished work.

## Six steps for each program

1. **Inspect BASIC.** Read the entire original `.bas` listing and relevant
   tape, screenshots, controls, timing and replay notes. Establish actual
   behavior, calculations, DATA/UDGs, input/output, color, sound, animation
   and end states. Compare with genuine BASIC execution where needed.
2. **Translate.** Put faithful C48 sources and optional glyphs under its
   `C48/`. Use frozen C48 APIs and `c48lib`. Keep temporary matching assembly
   in ignored `build/tmp/`. Never change historical BASIC for a comparison.
3. **Develop and test.** After each source revision build once with
   `python build/build-c48.py NN-name`, run targeted tests and repair defects.
   Do not duplicate unchanged-source builds or manually maintain hashes.
   Describe meaningful differences and any open gaps in `C48/README.TXT`.
4. **Independently review.** On the latest complete BASIC and C48 sources,
   perform separate normal and adversarial audits. Check all significant
   calculations, behavior, edge cases, inputs, collision, state, restart,
   timing and end conditions. If a defect appears, fix, regress and repeat
   the affected checks. Never claim independent agents unless used.
5. **Final integration.** Exercise actual frozen ZX-UX gameplay and controls;
   compare genuine equivalent BASIC/C48 states; inspect leftover pixels,
   attributes, sprite trails, ghost text and stale messages. Use real bitmap
   and attribute captures where possible. Test the actual TZX with `yolo`
   before claiming that path passed. Run the full program tests on final
   source. A failure returns to step 3.
6. **Deliver ONCE.** Run the automatic gate, update the progress cursor and
   include the cursor in the **same** single commit as this completed program.
   Review the full proposed diff; reject any locked path or BASIC change.
   Run the available private checker, commit, fast-forward push, then read
   back remote HEAD, changed paths, port bytes and progress cursor. Run
   `--closeout`. Advance to the next numbered program only after success.

## Release commands (from `src/bonus/60-programs/`)

```sh
python build/port_progress.py status
python build/check-c48.py NN-name --system PATH/ZX-UX.tzx --sdk PATH/SDK
# Only after READY: update cursor BEFORE staging the single program commit
python build/port_progress.py complete NN-name
# Inspect full diff; run private checker; commit port AND progress in one push
python build/check-c48.py NN-name --system PATH/ZX-UX.tzx --sdk PATH/SDK --closeout
python build/port_progress.py status
```

A new program can be completed only after its current-version build, tape,
gameplay and visual tests actually pass. Prior reset-era PASS reports cannot
be reused as new acceptance. The automatic gate checks order, program files
and the progress cursor. Run `python build/test-port-progress.py` when
changing cursor logic.

Program-specific tests must emit these lines only after real assertions:

```
CHECK normal PASS
CHECK adversarial PASS
CHECK integration PASS
CHECK remnants PASS
```

`CHECK remnants NA` needs actual proof no display remnants can apply. The
single-build gate executes the tests, validates package and tape name, rejects
unauthorized paths and uses `C48/PORT-RESULT.txt` to record its result. A
compile or intro screenshot is not full fidelity. No manual signoffs,
`PORT-CHECK.json`, hash ledger, duplicate builds or repeated full scans.

**Interrupted or blocked ports:** Never advance the cursor for partial work.
An uncommitted port can be lost when the session ends; this follows the
one-commit-per-finished-program rule. An unpushed local cursor is NOT canonical.
Re-fetch GitHub `main` at every new chat. A failed checker, remote conflict,
missing tests, or closeout failure is a blocker, not a completed program.

**Checker scope:** Machine checks cannot by themselves prove that review was
rigorous or that untested gameplay behaves correctly. Describe real gaps;
never claim a check ran when it did not.
