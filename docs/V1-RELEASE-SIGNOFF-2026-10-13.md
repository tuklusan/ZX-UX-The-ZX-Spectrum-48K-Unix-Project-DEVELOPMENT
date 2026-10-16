# ZX-UX v1 — private release signoff (2026-10-13)

**Status: RELEASED IN PRIVATE GITHUB.** No public publication is authorized.
Canonical repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project`.
This is a record of tests actually executed, not a proposal or an earlier checkpoint.

## Exact revisions and delivered files

- **Fully tested source commit:** `b4a46b2bf56b93524fe67e4ed103c4e756418a95`.
- **Private release-delivery commit:** `b9207e2144cd00b41b2b945718ae4d64e383a2bf` (only `release/` changed from the tested source).
- **Delivery Git tree:** `fbbde58983c114d736a9ce6e8cf7f82a4638762f`.
- `release/` contains **310 directly usable files**, without ZIP wrapping: TAP, TZX, Z80, SSX and PNG files, plus the manifest, source notices and logs.
- `release/manifest.txt`: 29,286 bytes; SHA-256 `1285c3cd7e90adbc78b82834491ec06e0df88da7db112085a185e2320e95a8d5`. Its 309 file records passed independent local size and SHA-256 verification. The manifest itself makes the 310th file.
- The private GitHub delivery was independently checked: 38 new or modified Git blobs matched the locally reviewed bytes, five files were added, 33 changed, no release files were removed, and all 310 final remote paths and sizes were verified. The other 272 files retained their original Git blob identity.
- `release/ZX-UX.tzx`: 24,224 bytes, SHA-256 `27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b`.
- `release/ZX-UX.tap`: 23,986 bytes, SHA-256 `0ef221b1c6c68b487b591f42dbfd01db414114e61b9ed450a8b0595627fb976f`.
- `release/ZX-UX.z80`: 24,526 bytes, SHA-256 `d804a824bd16bbf3470ff0b1fbdf983400fd027cedcbacbd17c8a61e1a82d4e3`.

## Actual selected-source release verification

- Recovered the exact Git history and reconstructed a **clean checkout matching the private remote source HEAD and tree**, then used the canonical `tools/release_v1.py` without suppressing any required gate.
- Checked toolbox: SJASMPlus 1.24.0, SkoolKit 10.1, compiled C simulator, and SHA-256-checked 48K ROM, all outside Git. FUSE SDL **1.6.0** and its Debian libraries were inspected and operated outside the repository.
- **Release-driver tests: 47 PASS**, zero failures.
- **C48 conformance: 1,146 PASS, 0 FAIL, 0 ERROR** (both backends and strict coverage checks).
- **Kernel regression: 20 PASS**; the independent IX and per-process environment tests passed.
- **Native ZX-UX target cassette sessions: 74/74 PASS.** Independently, the new SDK VM passed **74/74 native** and **74/74 bytecode** runs. Program tape creation and screenshot gates also passed.
- **Fresh real FUSE SDL tape boot: PASS.** Actual newly built `ZX-UX.tzx` loaded under the checked 48K ROM, with the ZX-UX banner, console title and `login:` marker verified from the real screenshot. `release/fuse-login.png` SHA-256 `17df57187fff17cac3715a22a12731829cb2a692015833c7305dfe116ab9e764`; proof JSON and hashes are under `release/`.
- LM compiled successfully with the approved new C48 SDK into a 17,870-byte SSX1 file. The loader showed 10,322 bytes free and 21,151 bytes needed. The owner requires compilation only; LM was not executed and is not an outstanding release gate.
- Release packaging initially stopped on two **empty optional FUSE stdout/stderr** files although real boot had passed. The reviewed narrow fix skips copying only those empty optional logs; every other required output still gets non-empty checking. The final clean run ended with `Verified release` and exit status **0**. The final output has no zero-byte delivered files.
- Before the final GitHub write the unmodified private checker passed **492 self-tests** and its pre-write scan of exact release content, paths, command and revised commit message passed **31,232 checks**. No checker binaries, rules, historical executable formats or external tool packages were shipped.

## Historical graphics and scope

The 48 authentic old-SDK comparison images and the v1 release screenshots now have **48/48 plausible same-program subjects**. The previously misassigned `examples/maze` capture was corrected using separate `maze1982` compilation and tape names. `release/shots/maze1982.ZX-UX.png` visibly contains the diagonal-line graphics from `programs/c48/examples/maze.c`, not the playable game grid. Its SHA-256 is `38a23a4c40450005cba3685105e1de74e2c1b10ed0c053f7520918f84c9adc73`; authentic old-SDK reference `docs/visual-reference/old-sdk/examples/maze.png` SHA-256 is `47212b3a0d54e1065dcdb9c1de81127728796252e4e67175add4482be94540a4`.

The other 47 native screenshot bytes are unchanged from the previously inspected release screenshots. The earlier 48-case report remains a historical checkpoint and is superseded only for its Maze mapping failure. The separate **30 old-kernel PNG/6,912-byte SCR pairs** have correct program subjects and titles, but their often title-only early frames are **INCONCLUSIVE** for complete frame/graphics identity. Inconclusive capture-state differences are not proven v1 defects. No authentic image was fabricated or replaced by artwork.

## Operating and preservation limits

ZX-UX v1 targets the **ZX Spectrum 48K**. Tests ran in FUSE and the
checked emulators. A test on physical hardware was not requested.

The released files, instructions and license notices are in `release/`.
The GitHub repository remains private. Rebuilding uses the tested source
commit and checked tools identified above. Subsequent delivery and report
changes did not alter the SDK, kernel or C48 application source files.
LM compilation with the approved new SDK was sufficient.

Historical checkpoints such as `docs/V1-HANDOVER-2026-10-13.md` recorded a correct **unreleased** state at their earlier commits. They do not override this fully executed and GitHub-verified signoff.
