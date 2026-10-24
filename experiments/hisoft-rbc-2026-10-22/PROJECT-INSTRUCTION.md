# ZX-UX - RBC 60-program completion

## Goal

No paperwork. No bureaucracy. Quick, direct, surgical.

1. Refactor RBC; run focused checks; commit and push the refactor immediately.
2. Process all 60 preserved Spectrum BASIC games through RBC. In each numbered game's `C48/`, save either the successfully linked native `.ssx` or a short `README` stating the precise reason compilation failed. One outcome per game; no extra deliverables.
3. Stop when all 60 outcomes are committed to DEVELOPMENT `main`.

## Repository and boundaries

The only working repository is
https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT
on `main`; never use the similarly named repository without `-DEVELOPMENT`.
At session start read current remote HEAD/tree and applicable RBC source before edits. Reconcile newer work. GitHub `main`, not a temporary checkout, is delivery.
Preserve every original BASIC/TZX byte and the frozen ZX-UX beta-0.2.0, SDK, kernel, emulator and release. Do not modify the private checker or its rules.

## RBC input and syntax

RBC's external input is numbered ASCII Sinclair ZX Spectrum 48K BASIC only. A strict adapter recognizes the original keywords and converts ASCII to genuine Sinclair tokens; the compiler core sees tokens only. Validate the tokenized lines with the original 48K ROM syntax checker without executing the program. Abort invalid or ambiguous input with line and clear reason. Never guess keyword boundaries, insert spaces, repair source or accept another BASIC dialect: `FOR I=1TO10` fails; `FOR I=1 TO 10` is valid.

When using an original TZX input, extract its already-tokenized BASIC, convert faithfully to unambiguous ASCII and round-trip check the tokens before feeding that ASCII to RBC. Preserve numeric encodings, quoted token bytes, control codes, UDG characters and line meaning. If lossless conversion is impossible, fail with the reason; never substitute the paired `.bas` silently.

Recognize genuine 48K BASIC syntax, but refuse operations unsupported by ZX-UX (`LPRINT`, `LLIST`, Interface 1 storage/peripherals, etc.) with a clear compiler error; no silent substitutes.

## Simple safety policy

Reject executable numeric `USR` token `0xC0` and any machine-code calls. Permit `USR "a"` through `USR "u"` only as compile-time-resolvable UDG address calculations for `POKE`, including provably bounded offsets such as `USR "a"+8`; relocate all proved bytes into process-owned UDG storage (168 bytes). Fail unresolved or out-of-range UDG address expressions. Ignore tokens in non-executable quoted messages and remarks. Do not allow `VAL` to execute prohibited machine-code calls.

Allow ordinary `POKE`, including dynamic addresses, except locations known at compile time to be dangerous to protected ZX-UX or machine state. The programmer is responsible for other crashes. Keep BASIC line-number `GO TO`, `GO SUB` and `RUN` working.

## Execution and finish

Fix shared RBC defects first. Check in the working refactor immediately, then process each of the 60 games. Keep only its final `.ssx` or short failure `C48/README`; do not add screenshots, TZX outputs, C48 porting work, historical reports, acceptance ledgers, handovers, or signoffs. A failed conversion, unsupported feature, or compiler failure is a README outcome, not a fabricated pass. Do not overwrite the original game inputs.

Before publishing, check exact changes and commit text with the unchanged private checker. Fix checker rejections within four attempts; fast-forward only. Read back remote HEAD and files. Do not claim compilation passed without an actual compiled, linked `.ssx`.

Finished means exactly 60 game outcomes, each saved under its `C48/` and verified on DEVELOPMENT `main`. Report the number of SSX outputs and failure READMEs, then stop. No other completion criteria or background work.
