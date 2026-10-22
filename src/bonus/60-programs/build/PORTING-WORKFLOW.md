# BASIC-to-C48 workflow — v0.6

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

1. Read live GitHub `main` HEAD (not a remembered commit or a stale local
   mirror). Fetch `src/bonus/60-programs/PORTING-PROGRESS.json` and this
   workflow **from that same HEAD**. If local checkout differs, reconcile
   safely before using it; never discard unrelated local changes.
2. Run `python build/port_progress.py status` in the up-to-date workspace.
   The JSON file is the committed cursor: `completed` is a continuous prefix
   of 01–60, and `next_program` is the first not yet completed. Both are
   validated against the 60 actual numbered directories.
3. Confirm the last completed program's remote `C48/PORT-RESULT.txt` and
   committed source/SSX/TZX/tests exist, and that its commit passed closeout.
   If the GitHub cursor disagrees with committed results, **stop and repair
   the record**, rather than silently skipping or redoing work.
4. **Resume only `next_program`. Never re-port a `completed` program.**
   Existing experimental or pilot C48 files in a later numbered directory do
   not mark it complete; when its turn arrives, review and validate them under
   the current gate. If `next_program` is null, all 60 are complete.

Current baseline at workflow v0.6 adoption: `01-minelay` is completed on
GitHub in commit `82a3514539e35641c09e659d9a31b0d9da90d9e7`.
`02-fall-guy` is next. This paragraph is historical; always use the live
committed JSON rather than a copied summary or an earlier conversation.

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

`complete` refuses any program other than the next one, missing C48 binaries,
or missing `PORT-RESULT.txt` gate PASS markers. The checker refuses a
completed/out-of-order program at normal gate time. Its closeout accepts only
the newest completed program, checks the committed progress file as well as
that port's files, and checks remote `main` equals local HEAD. These safeguards
prevent a new chat from restarting a finished port and stop advancement on a
failed or unpublished port. Run `python build/test-port-progress.py` when
changing the cursor code; it does not build or emulate games.

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
