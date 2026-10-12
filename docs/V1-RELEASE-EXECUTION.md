# ZX-UX v1 delivery checkpoints

Baseline: GitHub main commit `19b037fe8e05187ef73f6858585a0d5e4bc8274b`.
Specification: C48 Rev 0.11.

## Language and compiler

The verified source report records 322 passing C48 executions. It links
116 specification paragraphs to specific passing assertions. There are
641 further required entries without direct proof and two entries with
explicitly undefined behavior. A linked assertion does not certify every
sentence in its paragraph.

Review all pending entries in batches. Separate source-language semantics,
diagnostics, libraries, runtime behavior, command options, review context,
and undefined cases. Add direct assertions where required. Preserve the
actual command, output, source hash, and tool identity. Never count a
compiler success as native execution.

The release command must run the C48 verifier using both output modes and
stop if required C48 tests remain pending. Reviewed text and
undefined behavior must be documented, not promoted to passing compiler
checks without an applicable assertion.

## Integration and historical screens

Use only the checked new SDK for LM. Record compiled size and the 48K load
limit. The new-SDK LM check does not imply the image ran on the target.

Run the applicable C48 sources on ZX-UX. Check exit status, program startup,
process state, input, files, graphics, and system calls. Use real historical
screens and new emulator captures. Record hashes and matching execution
states; an unmatched state remains inconclusive.

## Clean build and release

Check remote main before edits. Start from a clean checkout with an exact
source commit and tree. Preserve the private checker outside Git. Build and
check the native tape, disk image, snapshots, screenshots, and other outputs.

A verified FUSE 1.6.0 boot using the current build/ZX-UX.tzx and checked
48K ROM must show the banner, console title, and login prompt. Save the
real screenshot and hashes. System, SDK, compiler, language, native, visual,
and integration gates must also pass on the approved candidate.

Deliver approved native .tzx, .tap, .z80, .png, and .ssx files directly,
with a manifest, SHA-256 sums, loading steps, and license details. Keep the
release directory outside Git unless explicitly requested. Check final
bytes before publishing and verify the remote commit and release files.

## Decision

A clean release-script exit alone is not final v1 approval.
Complete all mandatory tests before publishing v1.
