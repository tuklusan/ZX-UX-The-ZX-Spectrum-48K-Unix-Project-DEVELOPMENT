# ZX-UX 60 games - current work

Only GitHub DEVELOPMENT main is authoritative:
https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT
Never use the similarly named other repository. At every session read current
HEAD/tree, workflow, tests and port cursor before changes. Preserve original
games and frozen ZX-UX beta-0.2.0, SDK, kernel, emulator and release.

## RBC: original 48K Sinclair BASIC only

The RBC command-line input is numbered ASCII Spectrum 48K BASIC. A strict
adapter converts only unambiguously delimited keywords and valid Spectrum
characters, numbers, DATA, REM, strings and DEF FN into original tokenized
line records. An isolated ORIGINAL 48K ROM then syntax-checks every line,
without running the program. Reject invalid or ambiguous source with line and
reason. Never insert spaces, guess syntax, repair source or accept extensions.
FOR I=1TO10 fails as an incomplete FOR; FOR I=1 TO 10 passes the tokenizer.
The compiler core accepts ONLY the resulting ROM-validated Sinclair tokens.

For each original TZX: extract its already-tokenized BASIC, detokenize
accurately to explicitly unambiguous ASCII and re-tokenize through the SAME
gate. Check exact significant token bytes, numeric caches, quoted data,
control characters and user graphics. If representation is not lossless,
report a conversion failure; do not silently use the paired BAS instead.

All 48K keywords are valid syntax. RBC must explicitly reject unsupported
ZX-UX behavior (including LPRINT, LLIST, Interface 1 storage/peripherals).
Never silently replace, ignore or emulate unsupported functionality.

## Safety, without overengineering

Ban executable numeric USR token 0xC0 in every context. The ONLY exception
is proven UDG-address use in POKE, such as USR "a", USR "a"+8 or bounded
equivalent expressions. Spectrum 48K UDG A-U use 21 x 8 bytes; resolve ALL
possible destinations and relocate proven offsets into ZX-UX process UDG
storage. Reject any unproved or out-of-UDG USR expression. Token checks
must distinguish actual executable tokens from quoted text, REM, hidden
number caches and other non-code data. No machine-code entry is permitted.

Ordinary POKE is allowed except for destinations known at compile time to
hit dangerous protected machine or ZX-UX state. Unknown dynamic addresses
are the programmer's responsibility: never require exhaustive proofs for
ordinary POKE. Keep actual UDG writes working. VAL must not evaluate a
forbidden numeric USR at runtime; safe numeric VAL remains supported.
GO TO, GO SUB and RUN target BASIC lines, not machine addresses.

## A - original BASIC: reverify all 121 inputs from zero

60 BAS, 60 original TZX and HELLO each need a new outcome: verified native
pass, justified exclusion or OPEN. All earlier runs and exclusions are
non-credit. A native pass proves adapter/ROM gate, compilation, SSX linking,
48K fit and startup, gameplay, controls, timing, graphics/remnants and
creation/loading of a NEW ZX-UX executable TZX. HELLO has smoke checks.
Unknown or incomplete checks stay OPEN. An unavoidable rejection may be
closed only with a short game-local C48/BASIC-EXCLUSION.txt giving exact
input, line and cause; exclusions never finish C48 ports.

Run FAST focused checks after a change, paired BATCH checks after fixes,
and FULL on all 121 inputs across all five shards at milestones and closure.
Do not mistake compiler success, CI green or boot screen for gameplay proof.

## B - faithful C48: independently reaccept 60 ports from zero

src/bonus/60-programs/PORTING-PROGRESS.json is the only acceptance cursor.
Start with 01-minelay. Existing source/tests may save work, but none of the
earlier accepted ports or pilots carry new acceptance. Work in order, one
fully checked port per commit. Compare actual original and native gameplay,
math, controls, edge cases, timing, sprites, screen remnants and real SSX/TZX.
Follow src/bonus/60-programs/build/PORTING-WORKFLOW.md.

## Minimal publication and end condition

Keep useful code, fresh program outputs and meaningful machine results;
delete obsolete reports, checkpoints, old builds and consumed Actions files.
Do not produce handovers or dated status paperwork. Preserve original BAS/TZX
bytes and all frozen beta files. Before push check exact paths, proposed text
and commit message with unchanged private checker; fix rejection in at most
four attempts. Recheck remote HEAD; fast-forward only; read back new remote
commit/tree, changed files and cursor. Remove completed workflow YAML and
run history only after verifying required outputs are saved on main.

Finish when A has zero OPEN inputs and every permitted input passes real
native gates, and B has 60/60 independently verified ports. Report A native
passes/exclusions/failures/unknowns out of 121 and B accepted/60, with next
blocker and actual check level. Work only in active sessions.
