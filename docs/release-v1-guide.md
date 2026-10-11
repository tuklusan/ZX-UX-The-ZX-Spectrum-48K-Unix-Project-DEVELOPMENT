# ZX-UX v1 release guide

This guide describes the checked release procedure for the Sinclair ZX Spectrum 48K. It is a procedure, not a report that the current revision has passed its release tests.

## Preconditions

Work from a clean, checked checkout of the intended GitHub `main` commit. Confirm its commit ID before starting. Keep the private checker, the checked assembler, SkoolKit, the C48 source collection, the tape tools, the Spectrum 48K ROM, FUSE, and FUSE support files outside the checkout. Inspect each external tool and its dependencies before use.

Run the supplied private checker self-tests. Check all inputs, scripts, commands, file paths, and final files before delivery. Keep the checker and its private data outside the Git checkout and release.

Use the checked new C48 SDK to build and test ZX-UX v1 programs. Keep separate records for C48 specification checks, image comparisons, and native program runs. The LM host test uses the new SDK only, under the agreed waiver. A host result does not prove native execution on the Spectrum.

## Mandatory release command

The strict entry point is `tools/release_v1_strict.py`. Use the same Python interpreter for the launcher and the nested independent FUSE verifier. Substitute the actual, individually checked external paths below. This example is not executable until those paths have been set correctly.

```sh
python3 -B tools/release_v1_strict.py \
  --checker /external/checker.py \
  --sjasm /external/sjasmplus \
  --sdk /external/c48-sdk \
  --tap2sna /external/tap2sna.py \
  --fuse-test-command 'python3 -B tests/fuse_boot.py --fuse /external/fuse-sdl --rom /external/48.rom --tape build/ZX-UX.tzx --assets /external/fuse-assets --libdir /external/fuse-libs --screen build/logs/fuse-login.png --expect-zxux-login --wait 45'
```

The strict launcher validates the FUSE command before the build. Its verifier must use the real newly built `build/ZX-UX.tzx`, the checked 48K ROM, FUSE running in Spectrum 48K mode, and exact ZX-UX login-screen markers. The guard checks the resulting capture and its JSON proof against the tape, screen, and ROM hashes. A successful emulator launch or an unrelated zero exit status is not a boot proof.

The base runner `tools/release_v1.py` builds the system and runs the system, SDK, tape, screenshot, and release checks. It stops on failed commands or file checks. Always use the strict launcher for the additional independent FUSE command and capture validation.

## Release decision and output

Do not mark ZX-UX v1 complete unless the current candidate has passed the applicable C48 specification tests, native C48 integration, state-matched visual cases, the new-SDK LM proof, the complete system suite, and an actual independent FUSE login boot. Document inconclusive visual cases and unresolved limitations rather than recording them as passes.

The build creates `build/ZX-UX.tzx`, `build/ZX-UX.tap`, `build/unix.bin`, and `build/fs.img`. Save the source commit, tool versions, executed tests, ROM and tape hashes, file sizes, screen capture origin, and logs. Verify the output manifest and complete delivery folder before publication.

Distribute verified native output files directly in their actual formats. Keep generated `release/` output outside version control unless the owner explicitly requests a commit of selected release files. Do not package unchecked or historical third-party material into the release. Preserve attribution and licenses.

FUSE setup and the previous boot record are documented in `docs/fuse-independent-boot.md`. The release still requires a fresh boot test of the current build.
