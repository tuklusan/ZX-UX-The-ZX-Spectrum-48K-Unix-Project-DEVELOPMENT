# ZX-UX v1 native C48 integration checkpoint — 12 October 2026

Source: GitHub `main` commit `8e526b99da6e9406705c47337eafcf6ca2f4154f`.
Source Git tree: `9cb6d3cc5d9df238fee5ea2c7fbec2f6682669f1`.
This checkpoint is not final release approval.

## Verified execution

The checked 48K toolbox rebuilt `build/unix.bin`, `build/fs.img`,
`build/ZX-UX.tap`, and `build/ZX-UX.tzx`. The ROM tape was converted
into a fresh `build/test.z80`. The boot-area static checks passed.
The system emulator suite recorded **20 PASS, 0 FAIL**. Native ZX-UX
integration, with checked-in C48 source freshly compiled by the new SDK,
recorded **73 PASS, 0 FAIL** scenarios in seven batches. Each scenario
was exercised through the ZX-UX cassette loader with actual emulator
execution; 73 corresponding captured program screenshots are in
`build/shots/`. This is different from merely compiling 73 programs.

The host C48 VM suite independently passed **73/73 native** and
**73/73 bytecode** sessions. The new compiler's separate specification-led
verifier recorded **850 PASS, 0 FAIL, 0 ERROR**, while **320 required**
Rev 0.11 paragraphs still lack linked assertions and two are explicitly
undefined. The mandatory language release gate returned nonzero and
correctly stopped release approval.

## Fresh real FUSE login verification

FUSE SDL 1.6.0 loaded the newly built `build/ZX-UX.tzx` through the
verified Spectrum 48K ROM. The independent `tests/fuse_boot.py` process
confirmed actual boot-banner, console-title, and login-prompt marker
positions and captured the emulator display. The test returned success.
These are authentic emulator bytes, not reconstructed reference images.

- New tape: `build/ZX-UX.tzx`, 24224 bytes,
  SHA-256 `27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b`.
- Spectrum ROM SHA-256:
  `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42`.
- Actual capture: `build/proofs/fuse-login-850.png`, 3348 bytes,
  SHA-256 `17df57187fff17cac3715a22a12731829cb2a692015833c7305dfe116ab9e764`.
- Verification metadata: `build/proofs/fuse-login-850.json`.

The output is byte-identical to an earlier checked tape and capture;
that identity is observed from hashes, not assumed as a new visual match.
This execution did not run the gated end-to-end clean release script.

## LM waiver

Using only the checked **new SDK**, the LM build produced an SSX1 image of
**17864 bytes** with a reported **21145-byte** load/run memory need.
The configured v1 load allowance is **14000 bytes**. It therefore has
compiler/output proof, **not** a confirmed native run on the 48K target.
No old SDK or kernel retest is required under the approved LM waiver.

## Remaining release gates

The language gate reports 320 pending C48 requirements. Historical
matched-screen checks are incomplete. Final approval requires a fresh
clean-build run, the mandatory real FUSE login test, and final file scans.
This checkpoint is not an approved v1 release.
