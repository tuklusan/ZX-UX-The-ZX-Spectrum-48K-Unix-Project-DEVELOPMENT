# Enhanced ZX-UX kernel — integrated source and one-time restricted-text repair

Date: 2026-10-13. Private integration checkpoint; **not** an additional tagged release.

## Origin and scope

- Canonical repository: `tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project`.
- Checked upstream `main` before integration: `91c1cbd2d7ca4cc2d210e914d4ec31aab5d55d3a`.
- Integrated kernel development: 11-commit series supplied by the owner; locally reviewed in the preceding integration commit. The independently updated SDK is retained.
- One-time owner-approved cleanup changes restricted terms across active source, history-preserving reference copies, specification text, and stored proof filenames. This is **not** permission to relax checker policy, change language semantics, rewrite remote history, or alter a prior tag.
- Active public ABI, executable header, and shell enhancements are as established by the enhanced-kernel integration. No new interface change is made by the restricted-text repair.

## Document identity and traceability

The two modified sentences in C48 specification section 84 replace a term with a neutral equivalent. The semantics remain the same. The original normative document SHA-256 was
`6368abb4126c01f598f4b533a4e2a0a46a7ce4790cce02d3decbfba59e150d7e`;
the updated document SHA-256 is
`0fa74eb904fce98bd095a2f6d8f4ef9b5bde1b082c5f89692e13e7a04f176f13`.

The standalone text and the affected clause digests, traceability identity, the two disposition records, their frozen review-file checksum, public API checks, and clean-checkout validation checksum have all been updated accordingly. Historical dated descriptions of earlier source revisions retain their historical hashes. Two recorded VM result logs were **renamed, not regenerated**; all 18 entries in their verification manifest retain their original verified bytes, sizes, and SHA-256.

The authoritative Word document rendered to **88 pages** before and after the edit. Only page 62 changed, in the two intended sentences. Page count and all other rendered pages match exactly; the updated page was visually inspected.

## Executed local checks

- Private checker: 492 self-tests and 9 workflow tests PASS; private rule-list bytes unchanged.
- Full working-tree inspection following the text cleanup: 377,208 checks PASS (before test-generated caches and build scratch output).
- Kernel rebuild: 8,186 bytes within the fixed 8,192-byte limit; 38 installed programs.
- Real ROM tape conversion through SkoolKit 10.1: PASS; regenerated TZX/TAP/Z80 hashes match the independently FUSE-booted checkpoint. This is **binary identity confirmation**, not a claim of a fresh FUSE run after the text change.
- `tests/test_boot_v1.py`: PASS; `tests/suite.py`: 31/31 PASS.
- C48 language conformance: 1,146 PASS, 0 FAIL, 0 ERROR against updated trace identity.
- `release_*checks.py`: 47/47 PASS.
- Historical verification manifest: 18/18 tracked entries match bytes, sizes, and SHA-256.

## Release boundary

The tracked `release/` for the previously completed v1 release and the existing beta tags remain historical, unchanged, and **not** reissued by this source-only milestone. A changed release requires a new clean driver execution, release verification records and an owner-approved version identifier. Legacy non-text formats remain excluded from active integration paths. The checker remains private and outside Git; it is distributed separately to the owner.

The remaining upstream enhanced-kernel advisory/open findings are not silently closed by this cleanup. Do not interpret this checkpoint or the amended trace identities as proof that a new tagged release was completed.
