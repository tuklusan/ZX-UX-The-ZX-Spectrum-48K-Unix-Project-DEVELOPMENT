# Original HiSoft BASIC 48K v1.1: compiler runtime pointer inventory

These diagnostics derive from the unchanged original `HiSoft_BASIC_v1.1_48K_compiler_only.tzx`.

- Original TZX SHA-256: `3958f9d7c45fc0d9a2d0b4a2a7c1aa7e0405fd90c9ed30f14fac37b6b47d6dec`
- Compiler CODE image: address `$5CF0`, 11,885 bytes, SHA-256 `b3fb20debb186d74ca10d1ec7b09f1bc4cf12b89e092e4aca81741c3e00c5793`
- `runtime-emitter-table.tsv`: 131 original pointer slots at `$77AF`, including 121 populated entries and 10 zero entries. Frontend names are provisional labels from a different HiSoft release.
- `hisoft-reviewed-table.ctl`: SkoolKit 10.1 control file; the 262-byte pointer table is classified as address words. Other code/data classifications are provisional.

Independent offline Pasmo reassembly of the corresponding annotated listing reproduced the 11,885 original bytes exactly. The annotated listing and its reproducer are not part of this Git checkpoint. Reassembly equality alone does not verify emitted runtime instructions, branches, data roles, or relocation rules. **Gate 8 remains unresolved.**
