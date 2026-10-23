# ZX-UX — 60 original BASIC programs: lossless policy and progress handover

**Prepared:** 2026-10-23 (America/Detroit). **Audience:** a fresh assistant session with no local workspace or previous-chat state. **Purpose:** preserve all the important decisions and unresolved work from the current discussion, alongside the newest live GitHub verification records. **Do not treat this handover as proof that the new policy has already been implemented.**

## 0. Opening instruction for the fresh session

Use **only** `https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT`, branch `main`, as the canonical development repository. Read its **live** HEAD, tree, `src/bonus/60-programs/PORTING-PROGRESS.json`, `src/bonus/60-programs/build/PORTING-WORKFLOW.md`, and `experiments/hisoft-rbc-2026-10-22/results/LATEST-RBC-FULL.json` **before editing or reporting a current score**. An old HEAD in this document is a verified point-in-time reference, never a substitute for reading remote state. Never fall back to the similarly named repository without `-DEVELOPMENT`. Do not assume any clone, temporary output, `/mnt/data` file, CI file, or previous container still exists. There is no background execution between chats.

The user has approved specific new RBC language-safety policy but **has not asked to alter the frozen beta-0.2.0 system**. Implement source/compiler changes only in permitted development paths, run the private checker unchanged, and publish only verified remote milestones. Preserve historical `.bas` and `.tzx` input files byte-for-byte. This handover request itself does not count as executing the new compiler tests or delivering 60 finished ZX-UX tapes.

## 1. Two separate deliverables; never conflate scores

**Track A — original Sinclair BASIC -> native RBC:** Compile all 60 original `.bas` files and all 60 original `.tzx` tapes plus HELLO: **121 distinct inputs**. Produce correctly linked SSX and, where a ZX-UX-format `.tzx` delivery is requested, generate and independently validate that separate tape packaging. Direct compilation, link, native foreground start, real gameplay, and output-tape packaging are **distinct obligations**; do not claim that one proves the next. Record per-input status, complete error, cause category, tool/input revision, output location, and native result. Do FAST after edits, BATCH after related repairs and FULL 121-input/five-shard at milestones, with genuine key/timing/game-state/screen comparisons. Keep failures and unknowns visible. Fix RBC or common runtime, **never original BASIC**.

**Track B — faithful C48 translations:** Completely independent: 60 C48 programs, accepting one verified port at a time. Read the live cursor and workflow. Last verified 3/60: ordinary port `01-minelay`; grandfathered pilots `25-galaxians` and `58-invaders`. Next ordinary entry `02-fall-guy`. Do not redo accepted ports or advance the cursor for incomplete ones. Each ordinary port must pass real C48 build, normal and adverse tests, native execution, equivalent original-state review, controls, and screen-remnant checks, then be committed with progress in one verified milestone.

**Frozen boundaries:** ZX-UX beta-0.2.0 SDK, kernel, emulator, and release files remain frozen; private checker and its complete case-insensitive restricted-word list remain unchanged. Run required checks on proposed text and commit messages; diagnose and correct genuine rejections within the four-attempt limit. Never bypass a persistent rejection or force-push. Before writes check live HEAD, proposed diff, test outcomes, checker; after writes verify remote HEAD and tree. Existing external build helpers are not permission to change frozen sources.

## 2. Most recent live GitHub state — important change from old conversations

At preparation, live `main` was verified at:

- **HEAD:** `9de2f4efea1cb2a8acc59603bdca37de36aefbc4`
- **Tree:** `c1dcd67401d856f8c24f7fe9c59b9c9418e5c260`
- **HEAD report:** `experiments/hisoft-rbc-2026-10-22/results/RBC-NATIVE-SUBSET-2026-10-23.md`
- **Latest FULL results:** `experiments/hisoft-rbc-2026-10-22/results/LATEST-RBC-FULL.json`
- **Results source revision:** `1c96559ba5ff3ba423374f68e15e914d9d30838c`
- **Actions run:** `40031609347`
- **121/121 per-input records present; 111/121 passed the current combined compilation/link/native memory-approval gate.** This consists of HELLO plus both input forms of **55 of 60 games**. Both `.bas`/`.tzx` paths of five named games failed the enforced **14,000-byte native memory size limit**: ten total failed inputs. All 55 accepted tape executables have native foreground starts and nonempty screen verification records; these are not proofs of complete gameplay.
- **Five blocked titles and measured required bytes (tape/text respectively):** `13-radio-power` 18,692/18,695; `19-hobday-expenses` 18,061/18,076; `22-top-trainer` 20,383/20,383; `27-picture-pairs` 19,511/19,518; `41-asset-stripper` 18,951/18,951. Never simply raise the frozen system capacity claim to mask these failures.
- **Scuba** (`14-scuba`) and **Evolution 1** (`44-evolution-1`) now compile from both original forms and start on native ZX-UX under the implementation and rules tested by that FULL run. The earlier 117/121 score from `b097b375f279e53e0d3adfda7a5665b9b6afaa04` and its earlier Scuba/Evolution errors is **obsolete as a current checkpoint**. The new 111/121 is stricter *native size-approved* acceptance, not verification records of an unexplained parser regression.
- **Track B remains 3/60 accepted**, next `02-fall-guy`, confirmed by live `PORTING-PROGRESS.json` at this checkpoint.
- The newest validated RBC workflow outputs `rbc PROGRAM.bas` -> native `.ssx`; `-S` -> Z80 `.s`; `-c` -> linkable `.sso`; `--fit` is now default. RBC remains an experimental compiler built by the checked preparation scripts and fixed input tools, **not a release replacement for frozen RCC**. It does not assert a BASIC bytecode backend or automatic native/bytecode fallback.
- **Crucially, the new restrictions in Sections 3–5 below were agreed in this chat but have not been demonstrated by any updated FULL run. Do not claim all 55 currently passing programs comply, or that all 60 will ultimately be deliverable without knowing the audit results.**

GitHub source links:

- https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT
- https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT/blob/main/experiments/hisoft-rbc-2026-10-22/results/RBC-NATIVE-SUBSET-2026-10-23.md
- https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT/blob/main/experiments/hisoft-rbc-2026-10-22/results/LATEST-RBC-FULL.json
- https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT/blob/main/src/bonus/60-programs/PORTING-PROGRESS.json

## 3. Approved decision: multi-part BASIC / tape chaining is OUT OF SCOPE

**User (verbatim):**

> 1) Multi-part BASIC programs (more than one program) are not supported. The user can compile them separately and make tapes out of them using offline tools.

Operational interpretation accepted in this discussion:

- RBC compiles **each original BASIC listing** as a self-contained unit.
- Do not require one part to load, launch, or chain into a separately stored later part. In particular, **cross-tape** `LOAD ""` handover in the Evolution series is no longer a completion gate.
- This exception **does not** exempt actions wholly inside the same source listing: `RUN 130` must remain supported. Nor does it reduce 121 input records.
- A user may concatenate or package separately compiled executables with offline tape tools.
- Historical C48 Track B fidelity and gameplay gates remain independent; do not automatically impose an unsupported cross-program BASIC requirement on the RBC gate.

**Current implementation note:** `stage/native_run_rt.py` at the verified HEAD supports bare `RUN` and provably constant `RUN` line targets (next-existing-line semantics), restores stack, clears variables, resets DATA/READ, and branches to the corresponding original BASIC line; computed RUN targets remain unsupported. The older error `RUN argument` in Evolution 1 is no longer the active blocker.

## 4. Approved decision: machine-code invocation via numeric USR fails at compilation

**User (verbatim):**

> I am also thinking of making all BASIC statements that would cause a low-level jump to aritrary machine addresses to be unsupported. Can you list the BASIC statements that call the processor to jump to a given address that is the argument of those statements?

**Assistant's distinction, subsequently accepted:** Sinclair Spectrum BASIC uses **numeric `USR`** as the machine-code execution mechanism. `RANDOMIZE USR 32768`, `PRINT USR 32768`, `LET A=USR 32768`, `GO TO USR 32768`, and conditional expressions containing numeric `USR` are **all machine-code calls** even though the enclosing statement names differ. The restriction belongs to `USR` as an expression, not to `RANDOMIZE`, `PRINT`, `LET`, or `GO TO` generally. Normal BASIC `GO TO`/`GO SUB`/`RUN` are line-number control flow, not raw Z80 jumps. `POKE` is memory writing, not itself a direct machine-code jump (although writing code or vectors can indirectly affect execution).

**Important exception:** `USR "a"` in Spectrum BASIC yields the address of user-defined graphics character 'a'; it does **not** jump to executable code. This benign string form remains supported. Do not silently collapse that distinction when interpreting the user's subsequent phrase "if USR is seen"; the final assistant explanation explicitly retained the string exception, and the user agreed to the entire explanation.

**User (verbatim):**

> Agreed fully with failing compilation with proper reason feedback if USR is seen in the input code.

**Final intent:** reject **numeric `USR`** in any BASIC expression position, with line number and explanation of unsupported arbitrary machine-code execution; accept `USR` with a proven graphics-character string argument. Analyze tokens, not mere occurrences in `REM` or printed messages. If expression-valued strings are compiled/evaluated via `VAL` or equivalent, prevent dynamic construction from evading this policy. Reject or explain when type cannot be proven safe; never add arbitrary Z80 execution to satisfy a particular source.

Suggested diagnostic:

```text
RBC E_MACHINE_CODE:
Line 150: Numeric USR is unsupported.
Direct execution of machine code is prohibited.
```

## 5. Approved decision: POKE addresses MUST be statically provable, then memory-safety checked

**User (verbatim):**

> OK, that may not be out of scope unless it gets too confusing or complicated to figure out what a program is doing pokes and peeks.
>
> I am also thinking of making all BASIC statements that would cause a low-level jump to aritrary machine addresses to be unsupported. Can you list the BASIC statements that call the processor to jump to a given address that is the argument of those statements?

(Note: first line above is from the same user message as the USR question; it refers to potentially supported Scuba PEEK/POKE analysis.)

**User (verbatim, specific POKE rule):**

> Now, about POKE, I want you to fail if you are not able to resolve the exact address that it resolves to at compile time. Of course, a second check will be what to do with the resolved address, and fail if something dangerous to ZX-UX is being attempted, or handle it smartly, or fail intelligently, but that part is already implemented. Thoughts?

**Assistant's complete substantive policy, user then explicitly accepted 100%:**

1. Resolve the `POKE` target address at compile time, allowing literal expressions, constant propagation, and bounded loops.
2. **Prove every possible address** (one address or an **exact finite address set** determined from the original BASIC control flow and loop bounds). A simple min/max envelope is insufficient if the candidate addresses have gaps or include unproved members.
3. Fail compilation with precise cause, BASIC line and expression when the address depends on unknown keyboard input, unpredictable state, unbounded arithmetic, a dynamic variable not provably bounded, or analysis too complex to prove safely. This is a conscious compatibility tradeoff; no unrestricted runtime fallback and no unbounded theorem prover.
4. For each proved address, **apply the existing ZX-UX memory-safety policy as an independent second stage**: permit, faithfully virtualize or translate, or reject an unsafe write with a distinct diagnostic. Do not bypass or weaken the already implemented safety checks just to increase pass counts.
5. `PEEK` and related memory accesses are not blanket-banned in this decision; keep their existing safety checks, subject to faithful interpretation. A future tightening of `PEEK` is a separate policy choice, not an implied new rule.
6. Prove and preserve true BASIC runtime semantics for arrays, loops, branches, graphics, and character-set effects. Do not alter the original BASIC texts/tapes.

**User (verbatim confirmation):**

> Agree 100% with everything in your last response!

Approved Scuba examples:

| BASIC statement | Statically provable POKE destination(s) |
| --- | --- |
| `POKE 23606,0` | exactly 23606 |
| `POKE 23607,60` | exactly 23607 |
| `POKE 60256+(K+33)*8+J,A` where outer K=0..12 and inner J=0..7 | exact set of 104 targets, 60520–60623 |
| `POKE 60000+X,PEEK (15104+X)` where X=256..1023 | exact set of 768 targets, 60256–61023 |

Error examples from approved assistant reply:

```text
RBC E_POKE_ADDRESS:
Line 420: Cannot determine all possible POKE
target addresses at compile time.
Expression: 50000+A
Reason: A has no provable bounded value.
```

```text
RBC E_POKE_PROTECTED:
Line 632: POKE target 23606 is known,
but the requested memory operation is not
supported by the ZX-UX memory policy.
```

The exact error identifier strings above are **illustrative**, not proof that code with these diagnostics exists. Real errors must identify the true failing line and reason.

## 6. Scuba audit: embedded graphics DATA, not apparent executable Z80 machine code

**User (verbatim):**

> 2) Does scuba seem to have embedded machine code in it?

The source inspected was the entire preserved 7,913-byte original listing at:

`src/bonus/60-programs/14-scuba/BASIC/14-scuba.bas`

Git blob SHA `ee639609a45a825683650926527a725ce4ea7d81`, identical `src/` and `dist/` content at the time of review. Source link:
https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT/blob/main/src/bonus/60-programs/14-scuba/BASIC/14-scuba.bas

Findings from the actual listing:

- Lines 5010–6140: numeric `DATA` encodes **13 separate 8x8 bitmap graphics glyphs** (swimmer, small fish, sharks, weeds), not demonstrated Z80 instructions.
- Lines 5000–5009: `FOR K=0 TO 12`, `FOR J=0 TO 7`, `READ A`, `POKE 60256+(K+33)*8+J,A`. Exactly 104 graphics bytes are written.
- Lines 8999–9060: copy original Spectrum ROM glyph bitmap bytes into RAM using `FOR X=256 TO 1023: POKE 60000+X,PEEK (15104+X)`. Source and target addresses are finite and statically provable.
- Line 3270 sets the ROM/Spectrum character-set pointer to the copied RAM character bank using `POKE 23606,96:POKE 23607,235`; lines 3000 and 632 set it back to ROM using `POKE 23606,0:POKE 23607,60`.
- Line 5 changes a system variable for caps-lock mode, `POKE 23658,255`.
- **No `USR` machine-code execution calls or machine-code entry points were apparent in Scuba.** There is no justified requirement to execute embedded Z80 to support Scuba. Its `DATA` is graphical bitmap bytes, not assumed executable code.
- The correct RBC treatment is to recognize the intended character-system effects, prove destinations, and apply existing protected-memory handling or faithfully translate them; if safe behavior cannot be proven, emit a specific compilation failure.
- The subsequently verified run from source `1c96559...` already compiles and native-starts Scuba with a private writable character bank **under the existing compiler behavior**. The new POKE rule still needs a separate full audit; do not treat it as already tested merely because Scuba passed.

## 7. Open question asked immediately before this handover

**User (verbatim):**

> We are close enough to completion with the first set of 60-programs. Are you saying all 60 will be SSX'd and ZX-UX tzx'd, then, even with the stricter rules we just defined?

The prior assistant **had not finished answering** this question when the user requested the handover. It did issue this partial, durable answer:

> Not as a guarantee. The stricter rules may deliberately reject some of the 60 programs even if the previous compiler accepted them. I’ll check the preserved listings for numeric `USR` and harder-to-prove `POKE` addresses, then distinguish what is already demonstrated from what remains a goal.

Then GitHub's complete current tree was checked: exactly **60 preserved `src/bonus/60-programs/NN-.../BASIC/NN-....bas` listings** exist. The tool returned filenames and blob SHAs for all 60; **no completed all-60 token-level audit of numeric `USR` and dynamic `POKE` occurred in this discussion**. Do not imply otherwise.

**Required definitive answer on resumption:** **No, not yet guaranteed.** The project target is 60 original programs compiled to SSX and, if requested, independently proven packaged into ZX-UX TZX outputs; but today only 55 of 60 have size-approved native execution starts, five fail the proven capacity requirement, full gameplay and output-tape packaging are not fully demonstrated, and the newly agreed numeric-`USR` ban and compile-time-POKE-address proof have **not** been implemented and rerun against the corpus. Those rules can intentionally cause additional failures. A safe, honest completion claim requires re-auditing the entire corpus and both original input forms under the new policy, resolving permitted defects, respecting memory constraints, packaging actual output tapes, and passing native/gameplay/tape checks. Don't promise 60/60 before verification records. Fail any fundamentally incompatible program with precise reason rather than loosening safety.

## 8. Recommended next actions — in priority order, without speculative success claims

1. Verify fresh GitHub `main` identity, HEAD/tree, committed progress and latest FULL result. Reconcile any newer work. At last check, HEAD `9de2f4e...` contained a complete FULL 111/121 record; newer commits may exist.
2. Produce an auditable **token-aware** inventory for all 60 original `.bas` listings **and** their `.tzx` tokenized counterparts: numeric versus character-address `USR`, each `POKE` statement and expression, existing result, whether address set can be proved exactly, memory-policy disposition, source line and reason. Respect comments and strings. This audit has **not** been done in this discussion; classify unknowns as unknown.
3. Implement precise numeric-`USR` rejection (retaining safe string `USR`), with tests for every expression context and for non-code mentions in `REM`/strings; test source and tokenized tape. Reject unknown/mixed types safely and transparently.
4. Add compile-time POKE-address proof that supports constants, basic constant propagation, and statically proved bounded loops; exact finite target sets; fall back to **compilation error**, never unrestricted runtime write. Invoke existing memory policy after successful proof. Test Scuba and other cases, including unsafe branches, unknown induction variables, aliasing, dynamic expressions, and misleading min/max-only proofs.
5. FAST focused tests + HELLO + impacted programs and previously passing regressions; BATCH paired `.bas`/`.tzx` with native starts; FULL all 121 inputs/five-shard suite at milestone. Preserve structured errors and distinguish compile, native fit/start, game-state, screen remnants and TZX packaging.
6. Investigate five measured >14,000-byte programs with compiler-owned code-size/runtime efficiency (sharing routines, reducing fixed font overhead where safe), **not frozen loader/kernel changes**. Keep all failure records if fitting cannot be achieved.
7. Audit real output `.ssx` and ZX-UX-format `.tzx` generation/delivery rather than presuming an original BASIC input `.tzx` is a freshly generated native executable tape. Verify these tapes actually load/start where required, and do real gameplay/visual checks before describing a program as fully validated.
8. Independently advance Track B's `02-fall-guy` through its mandated native and fidelity gate and one checked remote acceptance, not through Track A verification records.
9. Do not push source changes without checking exact live HEAD, applicable tests, proposed diff, unmodified checker and approved message. Verify post-commit GitHub HEAD/tree and retain long-lived results remotely. Do not claim asynchronous work or fictitious screenshots.

## 9. verification records/notes from the current discussion (exactly what was and was not executed)

- Read live remote HEAD and complete recursive tree: exactly 60 original BAS listings visible; no missing listings found in this structural check.
- Fetched and reviewed the original Scuba `.bas`, read its POKE/PEEK/DATA/graphics operations; **not** a byte-by-byte runtime semantics proof for all execution paths.
- Fetched live C48 cursor and workflow: completed `01-minelay`, pilot-completed `25-galaxians`, `58-invaders`, next `02-fall-guy`.
- Read latest RBC FULL file and new native subset report from HEAD `9de2f4e...`, checked its revision/counts and explicit memory rejections; this is the newer status than historical `b097b375...`.
- Fetched `stage/native_run_rt.py` and verified literal `RUN` target semantics are present. No edits to RBC, frozen source, original BAS/TZX, tests or checker were made during this chat up to the handover.
- **No** all-60 fresh USR/POKE static audit, newly tightened checker run, new FULL run, tape packaging run, screenshot review, or new C48 acceptance was performed as part of this discussion.

## 10. Short prompt to paste into a new conversation

> Resume the ZX-UX 60-program work from `experiments/hisoft-rbc-2026-10-22/HANDOVER-POLICY-2026-10-23.md` in the sole canonical development GitHub repository `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT`, branch `main`. Verify LIVE main HEAD/tree, `LATEST-RBC-FULL.json`, and `PORTING-PROGRESS.json`; never overwrite intervening work. New mandatory RBC language rules: reject numeric `USR` at compile time with precise error, retain nonexecuting `USR "a"`; statically prove every possible target address of each `POKE` (including exact finite bounded-loop sets) or reject, then apply unchanged protected-memory policy. Multiple separate BASIC tape parts need not chain/load each other; same-listing `RUN 130` remains supported. Preserve all original BAS/TZX bytes and frozen beta-0.2.0; keep the private checker unchanged. The last verified FULL accepted 111/121 inputs (55 games both paths plus HELLO), with 10 failures across five oversized titles; Scuba and Evolution 1 now compile and native-start. C48: 3/60 accepted, `02-fall-guy` next. Re-audit all 60 under the NEW rules, preserve errors/unknowns, distinguish SSX linking, native gameplay, and actual ZX-UX TZX output; do not promise that all 60 will pass before it is demonstrated. Continue within the active session and publish only checked results.

---

**Preservation scope:** This handover records all user decisions, the assistant's accepted refinements, tested source findings, current remote status, limitations, the unanswered delivery question, and actionable resumption. It is not a literal export of hidden tool calls or platform-generated UI state. Its past SHA references remain valid historical checkpoints; new work must always start by reading live `main`.
