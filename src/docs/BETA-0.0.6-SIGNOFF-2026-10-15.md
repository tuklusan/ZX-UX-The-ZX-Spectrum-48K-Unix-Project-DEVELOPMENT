# ZX-UX beta-0.0.6 — private release signoff (2026-10-15)

Canonical repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT` (private; repository ID `1412173246`; branch `main`). This remains the sole canonical development and permanent release-storage repository.

Verified release build source: `b97872136651732c6bc7651240937ae8c62ed9e3` (tree `d65d62da08a56c1ad53cfaaa69ca279980d025cc`).
Canonical source merge after repository rename: `f06f260e790d361190924d77c24badefaa4d7c3d` (same source tree, with parents `b97872136651732c6bc7651240937ae8c62ed9e3` and `fddebdb053774de054ce47bb177684c6e0c8f165`).
Release delivery commit: `f85ce0cb9853d3928bc52a90eb0abc12c9249c10` (tree `57d01769037fbaf1f4e965083ea4a8852339f716`).

## Permanent release files

GitHub's `release/` contains **321 tracked files**: 320 entries in `release/manifest.txt` plus the manifest. Every entry's path, Git blob SHA, and exact byte size was compared against the live remote release commit, with no mismatches or unapproved extra paths. All 320 files' SHA-256 digests were independently checked against the same manifest in the exact local release checkout. Cryptographic equality of the remote Git blobs to those local files connects that verification to the remote release.

The SHA-256 digest of `release/manifest.txt` is `2be4409a32937383d207828b53cb0c2efbd277d876251319a279381612326693`. Release media, screenshots, native executables, logs, test records, hashes, source identity, tool versions, loading instructions, limitations and attribution remain as recorded in `release/`. The verified three-block tape loader is unchanged; future tape optimization is outside this release.

## Release validation results

The source-bound standalone release execution completed with exit status 0. Its records report 50 release-driver self-tests PASS, 1,146 C48 language checks PASS, 46 system regressions PASS, 74 native ZX-UX program runs PASS, 74 native VM runs PASS and 74 bytecode VM runs PASS. The kernel is 8,161 bytes (under 8,192 bytes); the low-memory kernel is 177 bytes. The independent FUSE SDL 1.6.0 boot using the checked 48K ROM produced the boot banner, console title and `login:`. The LM program compiled successfully; its execution is excluded under the approved v1 waiver. This signoff does **not** assert a fresh emulator run after GitHub publication.

GitHub Actions `Regression` run `38692247218` on the release commit did **not** complete successfully: the build, committed C48 tape verification and snapshot checks succeeded, but the final workflow-file upload failed because GitHub reported that its allocated Actions storage quota had been reached. The workflow overall status is FAIL, not a new PASS. All 321 required release files are permanently committed and Git blob-verified under the private repository's `release/` path rather than depending on the unsuccessful workflow upload.

The private checker passed its self-tests and retry-companion tests. Exact source and release pre-write checks passed before publication. GitHub's two branch updates were non-force with exact expected HEAD checks; the final release commit preserves the source integration, FUSE boot-fix and repository-rename history. Existing beta tags, licenses, attribution and v1 architecture remain intact.

## Private signoff and tag decision

**Approved for private `beta-0.0.6` tagging of this signoff commit only.** Create the tag once through the reviewed one-time workflow after verifying the triggering `main` commit, its parent, this signoff's blob, the release manifest, repository identity and an unused tag name. Never overwrite a tag, force-push or publish a distribution repository. Remove the one-time tagging workflow in a separate reviewed cleanup commit, preserving the tag target.
