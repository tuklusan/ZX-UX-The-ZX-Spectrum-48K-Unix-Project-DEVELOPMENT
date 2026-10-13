# ZX-UX v1 current-HEAD release checkpoint — 2026-10-13

Status: **UNRELEASED**, held by the mandatory C48 Rev 0.11 Appendix B interface gap.

Source commit: `d90eba790b28d31fc94e622fcdb08eea7c7b1b42`.
Source tree: `164856c20319566f0b86e880cb9ccc66f40e84b3`.
The 716 tracked source files were recovered and verified against the exact Git tree. The exact current-HEAD reconstructed Git checkout passed tracked-file and Git-tree integrity checks. The executable strict release driver completed with exit zero, but its public-API coverage was incomplete.

## Verified test records

- C48 verifier: 1,146 case executions PASS, zero FAIL, zero ERROR. Coverage: 647 linked paragraphs, 90 verified non-executable dispositions, 20 supported/documented target obligations, and two undefined cases excluded.
- Independent native ENV1: two sequential checks and a concurrent process-isolation check PASS, including cleanup and unique private storage addresses.
- Native kernel regression: 20 PASS, zero FAIL.
- C48 native application sessions: 73 of 73 PASS. Host native sessions: 73 of 73 PASS. Host bytecode sessions: 73 of 73 PASS.
- FUSE SDL 1.6.0 actual 48K tape boot: banner, console title, and login prompt PASS. Tape SHA-256 `27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b`. ROM SHA-256 `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42`. Screen SHA-256 `17df57187fff17cac3715a22a12731829cb2a692015833c7305dfe116ab9e764`.
- The candidate manifest listed 298 files, all size/hash verified. Its C48 PASS/FAIL word-count defect was identified; the proposed code correction remains a private, unpushed checkpoint. The original C48 test JSON is unchanged.
- The large LM program compiles with the new SDK (17,870-byte native image, 21,151 bytes required). The native loader independently rejects it with 10,322 bytes free, restoring the same free-memory count. The program itself was not executed, per the scoped memory exception.
- Historic frame comparisons: 48 pairs lack synchronized input, timing and random-state records. Behavioral equivalence remains INCONCLUSIVE.

## Mandatory blocker

C48 Rev 0.11 Appendix B requires **73 public functions** in `<c48.h>`. The active SDK header declares only **52**. The existing `docs/SPEC-SDK-R2.md` explicitly records the remaining 21 as unimplemented public functions with link errors. The 21 missing entries are:

`chdir`, `dup`, `getcwd`, `getenv`, `ioctl`, `kill`, `list`, `open_typed`, `pipe`, `read_full`, `remove`, `rename`, `spawn`, `stat`, `tape_load`, `tape_save`, `time_get`, `time_set`, `wait`, `write`, `write_full`.

The new `tests/release_public_api_checks.py` verifies the 73-entry inventory and checks both public declarations and runtime implementations. Its positive parser case passes. Its current-source completeness check correctly fails and will continue to block strict self-tests until the missing entries are implemented and tested, or an authorized specification change resolves the obligation. No types or interfaces have been guessed.

The generated tape, snapshot, native objects, captures, and logs remain a marked **private engineering checkpoint**, not a final release. No remote binary delivery or public publication is authorized by this record.
