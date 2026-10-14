# ZX-UX beta-0.0.5 — private signoff (2026-10-14)

Repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project` (private).
Release source commit: `37b8a7f7a0f67f1cae4ab9b490085d51bb8d05c8`.
Release source tree: `8bbc5cf689c42ac0efc09c3856f40ca08179225b`.
Verified release-delivery commit: `41392d4ea6c2ae4280c9224d1281e8f79ed88ef9`.
Release-delivery tree: `f5111afad8c7f990609640b9afa29c5eee8bdd36`.

## Delivered release

The tracked `release/` directory holds 318 files: 317 files listed in `release/manifest.txt` plus the manifest. On 2026-10-14, every manifest path and recorded byte size was checked against the live GitHub tree; all 317 matched. The manifest records SHA-256 values, source identity, test outcomes and tool versions. The manifest's byte hashes were not independently recalculated in this signoff session.

The recorded build checkout commit `4adae86929832596ffce0f47eab1b8960b1a6fc7` has the same source tree as the canonical source commit above, according to the release manifest. Only release-delivery files changed between canonical source commit and the verified delivery commit.

## Recorded test results

The release logs report 50 release-driver self-tests PASS, 1,146 C48 conformance PASS, 37 kernel/system regression PASS, 74 native ZX-UX program sessions PASS, 74 C48 native VM PASS, and 74 C48 bytecode VM PASS. The FUSE SDL 1.6.0 independent tape boot is recorded PASS with actual boot-banner, console-title and login markers. Kernel size is 8,189 bytes, below the 8,192-byte limit. The LM application compiled; execution remains outside the approved v1 requirement. These counts come from existing release logs. No tests were run again for this signoff.

The GitHub Regression run for the source commit ended with a failure at its final hosted-file transfer stage because storage was full. The build and tracked-output comparison steps passed. The overall run status remains FAILURE.

No physical ZX Spectrum 48K was used for this verification. The existing release terms and attribution still apply. The previous v1 signoff describes a different source revision.

## Decision

**Approved for private beta-0.0.5 tagging of the signoff commit.** The one-time tag must be created only when the tag name is unused, at exactly the commit recording this signoff, without rewriting any existing tag or branch history. No public publication is authorized.
