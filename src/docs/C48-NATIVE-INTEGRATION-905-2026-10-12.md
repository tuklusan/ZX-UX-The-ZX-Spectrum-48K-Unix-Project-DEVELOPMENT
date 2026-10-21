# ZX-UX C48 native integration checkpoint — 12 October 2026

Source revision: `97a9eb210a38e5568af77ec2497228f3486a9117`.
Git tree: `ddbad19e30603175f3f33841a52d647caad430bc`.
These checks were run on the recovered exact source tree with the separately
verified 48K toolbox and independent FUSE SDL 1.6.0. This checkpoint is not
an approved final release.

## Compiler, runtime, and system results

The specification-led verifier passed **905** executions, with zero failures
and zero errors, on the required native and bytecode modes. There are **476**
linked C48 paragraphs, **281** required paragraphs with no linked assertion,
and two explicitly undefined paragraphs. The strict release-coverage gate
returned status 1. The 22 release unit tests passed. Both host VM suites
passed 73 of 73 sessions. The kernel system regression suite passed **20**
checks with no failures on a new ROM-loaded snapshot.

The checked new SDK compiled the 56 canonical programs into cassette images.
`tests/ssxrun.py` ran all **73 distinct scenarios** using new C48 compilation,
ZX-UX cassette loading, emulator execution, and program-screen capture.
Every distinct scenario passed. To keep test runs bounded, the tests were
split across seven command batches. Some cases appeared in more than one
batch; the unique program/test identifiers were checked against all 73
`runs.json` entries. The 73 emulator screenshots were byte-identical to the
previous checked source manifest. This says nothing about unaligned old
kernel execution states, which remain inconclusive.

## Actual independent ROM boot

FUSE SDL 1.6.0 loaded the freshly built `build/ZX-UX.tzx` using the checked
Spectrum 48K ROM. The test matched the ZX-UX banner, console heading and
login prompt in the actual captured image, returning success.

- Boot tape: `build/ZX-UX.tzx` (24224 bytes), SHA-256
  `27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b`.
- Spectrum ROM: SHA-256
  `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42`.
- Emulator capture: `build/proofs/fuse-login-905.png` (3348 bytes), SHA-256
  `17df57187fff17cac3715a22a12731829cb2a692015833c7305dfe116ab9e764`.
- Capture metadata: `build/proofs/fuse-login-905.json`, SHA-256
  `e2293587f583a27ced9a011a20ab059089a0d4865bb18296f325be8eaf147270`.
- Emulator snapshot: `build/test.z80` (24526 bytes), SHA-256
  `d804a824bd16bbf3470ff0b1fbdf983400fd027cedcbacbd17c8a61e1a82d4e3`.

## LM and remaining work

The new SDK produced the LM SSX1 image at 17864 bytes with a reported
21145-byte memory need. The configured native load allowance is 14000 bytes.
The required new-SDK compile proof passed; native loading was not confirmed.
No old compiler or kernel was rebuilt for this check.

The clean release workflow has not yet completed successfully. Language
coverage and comparison results remain incomplete. Generated test files
and verification logs are kept outside Git.
