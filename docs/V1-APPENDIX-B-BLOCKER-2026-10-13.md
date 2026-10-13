# ZX-UX v1 C48 Appendix B correction — 2026-10-13

Status: **UNRELEASED**. This is a source-identity and verification checkpoint, not final release approval.

## Controlling language document

The Git-tracked C48 Rev 0.11 DOCX has SHA-256 `6368abb4126c01f598f4b533a4e2a0a46a7ce4790cce02d3decbfba59e150d7e` at source commit `d90eba790b28d31fc94e622fcdb08eea7c7b1b42`. Its Appendix B lists **52 public names**. The DOCX directs readers to the checked C48 header for signatures and excludes omitted historical facilities from the v1 interface.

The accompanying `docs/C48-Language-Spec-Rev011-Standalone.txt` has a different, 73-name Appendix B. That standalone text is not a faithful representation of the controlling DOCX for this section. The previous text-only 73-name gate would wrongly reject the amended DOCX contract. The corrected `tests/release_public_api_checks.py` reads the actual DOCX bytes and checks their current 52 names against declarations and runtime exports. It also tests a deliberately incomplete inventory and rejects changed specification bytes.

Any proposal to expand the v1 public interface beyond the currently amended DOCX needs explicit specification approval and verified declarations, implementations, and tests. No historical interface is silently counted as a v1 implementation.

## Actual current-source engineering tests

At the verified `d90eba7` source revision, the complete standalone release runner returned zero. C48 case execution was 1,146 PASS, zero FAIL, zero ERROR; the reviewed language and target gates passed. Kernel regression completed 20 checks; 73 native cassette sessions, 73 host-native sessions and 73 bytecode sessions passed. Actual FUSE SDL 1.6.0 boot of the freshly built `build/ZX-UX.tzx` verified the banner, console title and login prompt. All observations have logs and hashes in the private checkpoint.

The new SDK compiled LM to a 17,870-byte native image requiring 21,151 bytes. The target loader had 10,322 bytes free and correctly rejected the load, leaving memory unchanged. **LM itself did not execute.** Historical image comparisons remain inconclusive without matched execution state.

A candidate manifest count-format defect was also found: a summary field named `FAIL` with value zero was counted as an occurrence of that word. A corrective patch remains private and has not passed the full pre-push gate. The previous standalone release-driver success does not certify an updated source revision or settle the visual/LM limitations.

Do not label these candidate outputs as an approved v1 release until all applicable final-revision checks and scope decisions are complete.
