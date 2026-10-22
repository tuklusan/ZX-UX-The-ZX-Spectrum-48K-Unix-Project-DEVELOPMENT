# BASIC-to-C48 workflow — v0.5

Applies to all 60 numbered Spectrum BASIC programs, in directory order 01–60.
Translate the actual program, not a substitute. Execute autonomously within the
current active session: **continue without approval prompts or pauses between
steps and programs**. **Zero progress chatter, narration or interim chat
feedback.** On completion report only the concise final outcome, GitHub commit,
and any genuine blockers. Do not promise unattended work after the session ends.

**Hard boundary:** ZX-UX `beta-0.2.0` is frozen. Write only inside
`src/bonus/60-programs/`. Preserve every original `BASIC/` file byte-for-byte.
Never modify the SDK, compiler, emulator, root scripts, `dist/`, or frozen
checks. Run frozen tools only with output in this workspace or in isolated
disposable copies. GitHub `main` is permanent storage.

## Six steps per program

1. **Inspect BASIC.** Read the entire `.bas` listing and historical tape,
   screenshots, controls and replay notes. Establish the actual program's
   rules, calculations, DATA/UDGs, input, output, color, timing, animation and
   end states. Compare against genuine BASIC execution when needed.
2. **Translate.** Put the faithful C48 source and optional glyphs under the
   numbered program's `C48/`. Use frozen C48 APIs and shared `c48lib`.
   Keep temporary same-basename assembly under ignored `build/tmp/`.
   Do not alter the originals to make comparisons pass.
3. **Develop with targeted tests.** Build once after each source change using
   `python build/build-c48.py NN-name`, run focused tests, correct C48 defects,
   and add regressions. Do not rebuild unchanged source just to duplicate an
   output or maintain separate digest records. Keep a brief `C48/README.TXT`
   for real differences and any unresolved issues.
4. **Independently review.** On the latest complete BASIC and C48 source,
   perform two distinct autonomous passes: **normal** (every relevant BASIC
   branch, calculation and observable behavior) and **adversarial** (invalid
   or extreme input, collisions, timing, state changes, end/restart, edges).
   Use separate review agents in parallel when available; otherwise conduct
   distinct passes without pretending other agents were used. Repair each
   discovered defect in C48, add a failing-then-passing test, and repeat the
   affected reviews. No human approval or human signoff is required.
5. **Final integration.** Run the port under the actual frozen ZX-UX kernel,
   test applicable states and controls, compare equivalent original/C48
   screens, and inspect for **leftover pixels, attributes, character fragments,
   trails, stale messages and erased objects**. Use bitmap/attribute checks
   where possible; treat timing, font and random differences carefully.
   Test loading the TZX with `yolo` before claiming that path works. Run the
   complete program-specific regression suite once on the final source.
   If anything fails, return to step 3 and repeat relevant checks.
6. **Deliver once.** Only after the complete final suite passes: run the
   automatic gate, examine the full Git diff (including deletions/renames),
   reject changes outside `src/bonus/60-programs/` or unrequested BASIC
   changes, run the available private checker, and make **one commit and push
   for the completed program**. Use fast-forward only; read back the remote
   HEAD, changed paths and files. Do not commit incremental fixes or start
   the next numbered program until the current one passes. An unfinished
   program is blocked, not finished; do not disguise unrun tests as passes.

## Automatic final gate — no checkboxes or extra paperwork

Each program's existing `C48/test-<stem>.py` should execute its real checks
with `--system PATH` and `--sdk PATH`, and print these lines **only after**
the respective assertions passed:

```
CHECK normal PASS
CHECK adversarial PASS
CHECK integration PASS
CHECK remnants PASS
```

For programs that never update their display, `CHECK remnants NA` is allowed
only when the test script verifies that the case does not apply. The program
may use a different test script through `--test PATH`. These lines replace
manual PASS fields; they cannot independently prove review thoroughness.

From `src/bonus/60-programs/`:

```sh
python build/check-c48.py NN-name --system PATH/ZX-UX.tzx --sdk PATH/SDK
# commit and fast-forward push only if READY
python build/check-c48.py NN-name --system PATH/ZX-UX.tzx --sdk PATH/SDK --closeout
```

The gate builds **once**, runs the program-specific tests using the actual
system, checks the SSX/TZX and tape name, rejects dirty or out-of-scope Git
changes, then prints all gate results and fails closed. At closeout it also
checks the live `origin/main` and committed file bytes. No manual JSON,
second build, repeated full-source scans or separate hash spreadsheet.

**Scope of the gate:** It can verify commands, outputs, test assertions and
Git delivery, but cannot prove that an independent review was rigorous or
that untested gameplay is correct. Record such gaps plainly and do not call
an incomplete port finished. Local uncommitted work can be lost if a session
ends; this is an explicit trade-off of the one-commit-per-completed-program
policy, not permission to make intermediate commits.
