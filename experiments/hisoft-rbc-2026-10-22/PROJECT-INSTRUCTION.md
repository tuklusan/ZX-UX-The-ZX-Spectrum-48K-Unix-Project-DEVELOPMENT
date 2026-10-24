# ZX-UX - reset 60-game plan (48K ROM BASIC gate)

## Source of truth and new baseline

Only https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT
`main` is authoritative. Never use the similarly named non-DEVELOPMENT repo.
At every session start read live HEAD/tree, latest RBC FULL result, C48
workflow and `src/bonus/60-programs/PORTING-PROGRESS.json`. Reconcile newer
remote changes before editing. Local containers are temporary, not delivery.

**Restart BOTH independent tracks from scratch under THIS design.** Earlier
RBC runs, BASIC exclusions, accepted C48 ports and pilot waivers are historical
results, not current acceptance. Keep original files, C48 implementations and test data for revalidation.
Start Track A at 0/121 new-policy native passes and 0 reapproved exclusions;
Track B at 0/60. Neither track completes the other. Do not add new goals.

## RBC - ASCII input, tokenized core, original ROM syntax gate

RBC's ONLY external source input is strict numbered ASCII Sinclair ZX
Spectrum 48K BASIC `.bas`. Its compiler CORE accepts ONLY validated original
Sinclair BASIC tokens and line records; it never parses or repairs ASCII.

Pipeline: ASCII -> strict 48K tokenizer -> isolated original 48K ROM syntax
check -> validated tokenized program -> RBC -> SSX -> ZX-UX executable TZX.
Prove the ROM check with actual 48K ROM behavior and reliable diagnostics;
NEVER RUN the source program during syntax validation. Do not claim input
accepted until this gate has actually passed.

Implement a minimal explicit-token ASCII adapter. Web emulator `public/basic.js` is a reference, not a complete parser. Encode all
original 48K keyword token bytes, original number format, BASIC line headers,
terminators, strings, DATA, REM, DEF FN and Spectrum character forms. Do NOT
guess a token buried in an identifier or adjacent to a number; never inject
spaces, repair source, or allow expanded BASIC dialects. `FOR I=1TO10`
MUST fail as an incomplete FOR statement, with line and error;
`FOR I=1 TO 10` is valid. Any ambiguous or invalid input aborts the gate.
The programmer must supply parsable ASCII.

Original `.tzx` tapes are references, NOT RBC inputs.
Extract their existing BASIC tokens unchanged, convert them to
unambiguous ASCII and pass that ASCII through the SAME adapter
and ROM gate. Verify token-level round trip, including numeric encodings,
quoted tokens and glyphs; fail clearly if lossless conversion is impossible.
Never secretly substitute a partnered `.bas` file. Original input tapes
are NOT newly generated ZX-UX executable output tapes.

Valid Spectrum syntax does not imply ZX-UX support. RBC explicitly refuses
valid but unsupported functions, e.g. `LPRINT`, `LLIST`, unsupported Interface
1 storage/peripheral operations, with line and reason. Never silently skip,
redirect or emulate a missing facility. Recognize the full original 48K
keyword set even when the target cannot implement the operation.

## Minimal safety policy - replace previous overly strict POKE policy

- Reject the executable Sinclair `USR` **TOKEN 0xC0** in every expression,
  whether numeric or `USR "a"` graphics form. Inspect original token context,
  not a spelling regex. Quoted strings and REM are not code; DATA may contain expressions.
  `VAL` must not execute tokens constructed in strings at runtime; either
  prove a safe evaluator or reject that unsafe use, not harmless VAL numbers.
- `POKE` is permitted by default. Refuse a **known** compile-time destination
  only if it demonstrably targets protected ZX-UX/kernel/machine state or
  another clearly dangerous reserved region. Permit ordinary graphics,
  attributes, UDG and game-memory POKEs. Do NOT reject a dynamic address
  merely because exhaustive compile-time proof is unavailable. Programmer
  bears responsibility for other POKE crashes. Preserve applicable PEEK
  handling without adding speculative blanket restrictions.
- Banning ALL executable `USR` also prohibits `USR "a"`. UDG must be supported
  with a proved USR-free facility, not an invisible source rewrite or a fake
  pass. Until that is available, affected games stay OPEN. A glyph byte
  equal to 0xC0 inside nonexecuted data is not by itself a `USR` statement.
- BASIC `GO TO`, `GO SUB`, `RUN` and computed BASIC line numbers are legal
  BASIC control flow, NOT machine-address jumps. Preserve loops, arrays,
  graphics, timing, game behavior, screen remnants and UDG effects.

## Track A - reverify 121 original inputs

Cover all 60 `.bas`, all 60 original `.tzx` and HELLO independently. Each
has ONE current outcome: verified native pass, reapproved documented
exclusion, or OPEN (failed/unknown). Old 111/121 FULL compile counts and
later frontend figures are non-credit historical results.

Permitted inputs require strict adapter/ROM validation, RBC compile, native
SSX link, real 48K memory fit and start, controls, timing, game-state
behavior, authentic graphics/remnants, new ZX-UX executable TZX creation
and loading. HELLO gets applicable smoke checks. Boot screens or successful
CI alone are not proof of gameplay. Never invent test results or images.

Only an unavoidable safety/unsupported-target or frozen-memory rejection may
close an input without native tests, AFTER investigation. Keep exactly ONE
short `C48/BASIC-EXCLUSION.txt` under that game's directory, naming its
affected BAS/TZX file(s), the original BASIC line or precise cause and why
current rules cannot permit it. Old notes remain historical pending review.
Do not duplicate exclusion prose into new reports or ledgers; normal machine
result data may record status/errors. A fixable adapter/RBC bug or missing
proof is OPEN, not an exclusion. An exclusion NEVER skips or accepts Track B.

## Track B - reaccept all 60 C48 ports

The ONLY cursor is `src/bonus/60-programs/PORTING-PROGRESS.json`, reset to
`completed: []`, `pilot_completed: []`, `next_program: 01-minelay`.
Formerly accepted `01-minelay`, `25-galaxians` and `58-invaders` retain useful
sources/tests, but NONE carry completion or a pilot exemption now. Follow
`src/bonus/60-programs/build/PORTING-WORKFLOW.md` and work in order, ONE
revalidated port per accepted publication. Compare original/C48 controls,
state transitions, calculations, timing, edges, graphics and screen remnants;
verify real native SSX/TZX loading/gameplay. Never advance an unfinished port.

## Efficient verification and publication

After RBC/adapter edits run FAST focused syntax/token/ROM, HELLO, USR, POKE,
VAL and regression tests. After related fixes run BATCH on paired BAS/TZX
plus native checks; run FULL across five shards/121 at milestones and final
Track A closure. Preserve genuine per-input failures/timeouts. Share stable
checked tool/input hashes instead of rebuilding everything unnecessarily.
Keep build, native and output-tape results separate.

Freeze original BAS/TZX bytes and ZX-UX `beta-0.2.0`, SDK, kernel, emulator,
and release. NEVER edit private checker or its restricted-word list. Before
each push read remote HEAD, inspect exact changes, run checks, and use the
unchanged checker on paths, contents and commit message. Fix rejection within
four attempts; never bypass it. Fast-forward only. After publication read
remote commit, tree, changed files and cursor. Store source,
executable outputs and results on DEVELOPMENT `main`. No duplicate builds.

Remove each consumed GitHub Actions workflow YAML and finished run history
ONLY after verifying all needed outputs/results are saved on `main`. Keep
workflows that future tests still need.

End condition: Track A has zero OPEN inputs, each permitted input passes all
native gates, each exclusion is justified and reapproved; Track B is 60/60
accepted; all deliverables are committed and read back on DEVELOPMENT main.
Report Track A native passes/exclusions/failures/unknowns out of 121 and
Track B accepted/60 separately, plus next blocker and actual check level.
Do not claim work done outside the active session.
