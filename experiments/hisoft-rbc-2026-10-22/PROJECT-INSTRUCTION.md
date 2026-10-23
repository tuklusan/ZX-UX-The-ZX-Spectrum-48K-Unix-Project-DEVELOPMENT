# ZX-UX - 60-program work plan

## Source of truth

The only working repository is
https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT
on `main`. Never use the similarly named repository without `-DEVELOPMENT`.
At the start of each session, read the live HEAD and tree, the latest RBC FULL
result, `src/bonus/60-programs/PORTING-PROGRESS.json`, and the C48 workflow.
Reconcile any newer remote work before editing. Never trust a previous clone,
container, local file or historical commit as current state. GitHub `main` is
the lasting home of approved work.

Complete the 60 preserved games in two independent tracks:
A - original BASIC compiled directly with RBC;
B - faithful C48 ports. Progress in one track never completes the other.
Do not add unrelated goals.

## Track A: closure rules

Cover all 121 original inputs: 60 `.bas`, 60 original `.tzx`, and HELLO.
Each input has exactly one final outcome: verified native pass, approved
exclusion, or still open. An input with an approved exclusion is **closed**,
not compiled or passed. The project is finished when there are no open
inputs, every permitted input passes its required native checks, and every
excluded input has a real reason saved as described below. A forced 121/121
compile-pass count is no longer required.

For a permitted input, prove compilation, SSX linking, real 48K memory fit,
native start, required controls and timing, real game-state behavior,
screen graphics and remnants, and actual ZX-UX executable TZX creation and
loading. An original BASIC input tape is not the newly built output tape.
HELLO gets its applicable smoke checks. A boot screen or green job is
not proof of complete gameplay. Never invent test results or screenshots.

An unavoidable rejection under the accepted compiler-safety rules or the
frozen native memory limits can close an input without native or output-tape
testing. Save ONE short `C48/BASIC-EXCLUSION.txt` in that numbered game's
directory, naming the affected BAS/TZX input(s), the original BASIC line or
other precise cause, and why current ZX-UX rules cannot permit it. A single
decisive cause is enough. This file is the sole lasting explanation for
the exclusion; do not copy that reason into compiler-output reports,
new status documents, or a separate exclusion ledger. The compiler must
still give a useful error when run. Automated run data may retain the
input status and error needed for repeatable testing, but does not replace
the `C48/` note. Never call an uninvestigated error, a fixable RBC defect,
or a missing test an unavoidable exclusion. Keep unknowns open.

A BASIC exclusion does NOT accept, skip, delay, or change the independent
C48 port. The `C48/` location is only a convenient home for the note.

Enforce the accepted safety policy in the development RBC:
- Reject numeric `USR` in every expression context, including through
  computed expressions; preserve harmless graphics-character `USR "a"`.
  Ignore non-code occurrences in remarks and quoted messages.
- Prove every possible POKE target address at compile time, including exact
  finite sets obtained from safe constant propagation and bounded loops.
  An unproved target fails compilation; never fall back to unchecked writes.
  Then apply the existing ZX-UX protected-memory policy as a separate gate.
- Do not let `VAL` or another computed expression bypass the rules. Keep
  existing PEEK safety treatment. Do not weaken checks for more passes.
- Preserve real BASIC semantics: loops, arrays, graphics, timing, RUN to
  another line in the same listing, and user-defined character effects.
  Separate multi-part BASIC programs need not chain/load from other tapes.

Fix shared RBC or runtime causes first, especially those affecting the most
inputs. Treat compilation, memory fit, foreground start, gameplay, and
output-tape packaging as different tests. The suite should retain its
existing per-input machine results and genuine failures. Do not create
duplicate prose reports merely to repeat compiler output.

## Track B: faithful C48 ports

Use `src/bonus/60-programs/PORTING-PROGRESS.json` as the only acceptance
cursor and `src/bonus/60-programs/build/PORTING-WORKFLOW.md` as the procedure.
Last recorded accepted: `01-minelay`, `25-galaxians`, `58-invaders`; check
live state before relying on this. The next regular port was `02-fall-guy`.
Never redo an accepted port or advance the cursor for an unfinished one.
Build and test the next port, compare actual original/C48 states, controls,
edge cases, timing, graphics and screen remnants, then verify real native
SSX/TZX operation. Accept and publish ONE completed port at a time with its
progress update. Keep the two existing pilot exceptions visible.

## Efficient checks and publication

After an RBC edit run FAST focused tests, HELLO, affected examples and prior
regressions. After a related fix run BATCH on paired BAS/TZX and native
checks. Run FULL, all five shards and 121 inputs, at milestones and before
final Track A closure; record approved exclusions as exclusions, not
compile passes. Skip native/gameplay/output tape work only for excluded
inputs. Share unchanged setup and checked tool/input hashes rather than
rebuilding it. One timeout must not erase other input results.

Preserve all original BAS and TZX bytes. Keep ZX-UX beta-0.2.0, its SDK,
kernel, emulator and release files frozen. Do not edit the private checker
or its case-insensitive restricted-word list. Check the proposed paths,
text and commit message with the unchanged checker. Fix an actual rejection
and retry within four attempts; never bypass a lasting rejection.

Before each push read current remote HEAD, run applicable checks, inspect
the exact changes, and refuse unexpected edits. Use a safe fast-forward
write only. After publication read the remote commit, tree, changed files
and progress back. Store only useful source, required program outputs,
the one-line-or-short exclusion notes, and meaningful test results on GitHub.
Avoid duplicate builds, status paperwork, handover files and ceremonial
signoffs. Never treat temporary local storage as delivery.

Report separately: Track A native passes, accepted exclusions, failures and
unknowns out of 121; Track B accepted ports out of 60. State the next actual
blocker and the check level really run. Work only during the active session;
do not promise unseen background work.
