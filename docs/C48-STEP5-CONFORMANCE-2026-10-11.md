# C48 v1 language-verifier checkpoint — 11 October 2026

**Status: Step 5 remains incomplete.**

Authoritative specification: `docs/04-C48 Language Specification Rev 0.11.docx`.
SHA-256: `577a93270fcd14efc13b4b2b2e6c7c08eaafd24efbd771199ed4a0278ec037ec`.

Run with the checked independent external toolchain, after building `sdk/lib/libc48.ssa`:

```
python3 tests/c48/conformance.py --backend both --report build/logs/c48-conformance.json
python3 sdk/tests/vm_reference.py --native
python3 sdk/tests/vm_reference.py --bytecode
```

The new standalone verifier has 252 source cases, with 56 native/bytecode cases executed twice. The October 11 candidate generated 308 PASS executions, zero FAIL, zero ERROR. It indexes 759 prose entries under 103 numbered specification sections and seven appendices. Only 106 of these entries had direct linked test assertions; 653 remain unexercised. An EXERCISED paragraph only means a specific linked assertion passed; it is not proof of all duties in that paragraph. The conservative required/undefined classification in `tests/c48/traceability.json` requires individual review. No language extensions are permitted by section 81. Missing coverage, float golden bytes, diagnostics precision, runtime libraries, and resource boundaries remain open.

The independent current-system host-VM regression passed 73/73 sessions in native mode and 73/73 in bytecode mode against checked-in screen SHA-256 values and execution states. These are **host runtime** tests; neither replaces a newly built native FUSE boot nor proves matched historical old-kernel execution.

Three fixes in the current SDK address specification defects:

- `sdk/rcc/z80gen.py`: emit a distinct object for each separate string-literal occurrence, including identical and suffix literals (section 15).
- `sdk/rcc/lex.py`: reject macro replacements that are not complete C48 compile-time constant expressions (section 71).
- `sdk/rcc/bcgen.py`: retain referenced scalar globals when a bytecode request falls back to native code in a float-using function.

Authentic historical comparison: `docs/step5-authentic-visual-audit.json` records independent hash and pixel checks for 22 old-SDK/new-SDK host image pairs. All 22 images match after exact 3x scaling, but original frame timing is not independently established. The other 26 historical SDK references and all 30 native old-kernel screen pairs lack matched-state completion. These cases are **inconclusive**, not passing. No visual files are fabricated or generated as historical proof.

The known LM exception remains: compiled on the new SDK; a runnable ZX Spectrum 48K load was not established because its measured memory requirement exceeded the configured load budget. Step 5 is therefore incomplete, and v1 should not be declared final based on this checkpoint.
