# Independent C48 SDK verification checkpoint

Date: 10 October 2026.
Base ZX-UX GitHub commit: `5455030c71f0a8d5c9c2d4a72a063bcf4afee23a`.

## Verified local results

- The repaired independent C48 compiler contains 94 checked files.
- The complete independent SDK unit suite passed: 422 tests, zero failures.
- All 56 standard C48 C programs compiled in the independent SDK layout.
- The LM compiled and ran in the repaired independent C48 SDK host VM.
- The LM test covered loading the unchanged 8,566-byte model, prompt input,
  line editing and a clean exit. Native execution on the 48K is not a v1
  requirement.
- Regenerated SDK source tapes: 57, validated by the SDK unit tests.
- The updated private checker passed 102 self-tests. It remains outside Git.
- The checked compiler tree and its ZIP checkpoint passed the private scan.

The complete checked compiler source is saved as
`ZX-UX-C48-compiler-422-tests-checkpoint-2026-10-10.zip`, with the files
under `c48-sdk/compiler/`. This is a source checkpoint, not the v1 release.

ZIP SHA-256:
`b391a786d37b9df23f6bd8caca7b13aecc66d6240d0e95953151077ac9f43f58`

This file records validation of the staged compiler only. It does not claim
that all 94 checked compiler files have been incorporated into GitHub.
The source ZIP is retained in the conversation and the owner's Library at
`/ZX-UX/ZX-UX-C48-compiler-422-tests-checkpoint-2026-10-10.zip`.

## Remaining gates

Import all checked compiler source files into the official GitHub tree and
verify every remote file. Complete the reference files and independent FUSE
boot checks. Run the cross-SDK and release script from a clean checkout.
Produce a native-file release with file sizes, SHA-256 values, source commit,
tool versions, and actual test results. Do not certify an untested release.
