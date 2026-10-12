# C48 specification verification checkpoint — 12 October 2026

Base repository commit: `5f32be318ac2093116a4ae20aa6f3d07b5b5753e`.
Specification: C48 Rev 0.11, SHA-256 `577a93270fcd14efc13b4b2b2e6c7c08eaafd24efbd771199ed4a0278ec037ec`.

Independent C48 check: 322 passes, zero failures.
Paragraphs: 759. Linked: 116. Pending: 643.

The grouped runtime fixture now refers to five real paragraph entries rather than seven section-heading identifiers. The verifier rejects invalid paragraph references before writing a report. The disposition generator now derives coverage counts from the supplied verified run, rather than assuming earlier counts.

A clean build from the base commit passed the repository release script, including 73 native and 73 bytecode host runtime cases, 73 on-target C48 emulator cases, the system suite, and an independent FUSE 1.6.0 boot to the ZX-UX login screen. The actual tape SHA-256 was `27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b` and the emulator capture SHA-256 was `17df57187fff17cac3715a22a12731829cb2a692015833c7305dfe116ab9e764`.

These checks are not a complete C48 conformance proof. LM compiles using the new SDK but exceeds the tested target load budget. Outstanding language requirements and historical comparison states prevent final v1 approval. No public release is claimed by this checkpoint.

## Later verified language batches — 12 October 2026

The C48 verifier on the current SDK passed **585 executions, with zero FAIL
and zero ERROR**, using both native and bytecode modes. Of 759 indexed
specification paragraphs, 302 have one or more linked passing assertions;
455 required paragraphs still lack direct proof, and two are explicitly
undefined. Passing an assertion proves only its checked behavior, not the
entire paragraph. The new tests reside in `tests/c48/spec_batch.py`,
`tests/c48/spec_batch2.py`, and `tests/c48/spec_batch3.py`. The checked-in
`tests/c48/dispositions.csv` is regenerated from this exact verifier run,
not inferred from paragraph headings or accepted source alone.

Build `sdk/lib/libc48.ssa` using the checked SDK toolbox, then run:

```
python3 sdk/lib/build.py
python3 tests/c48/conformance.py --backend both --report build/logs/c48-conformance.json
python3 tests/c48/coverage_gate.py --report build/logs/c48-conformance.json
```

The independent release-coverage gate correctly rejects this candidate
because the remaining required duties have not been proven. Earlier
execution and FUSE results apply to previous source revisions. The final
revision still needs new integration tests and matching historical frames.
The LM load-budget exception is unresolved. No v1 release is claimed.

## Further direct compiler assertions — 12 October 2026

A fourth specification-led batch exercises pointer initializers, numeric
conversions, storage initialization, expression semantics, and argument
order. The complete two-backend verifier now records **673 passing
executions**, with no failures or errors. There are 351 paragraphs with
specific linked assertions, 406 required paragraphs without linked proof,
and two explicitly undefined cases. The source of these additions is
`tests/c48/spec_batch4.py`; the updated disposition table is derived from
the verified 673-execution report, not inferred from accepted compilation.

The mandatory coverage gate still rejects v1 publication. The earlier
emulator results do not replace a fresh final-revision integration run.

## Fifth and sixth direct-assertion batches — 12 October 2026

The two new specification-led batches add `tests/c48/spec_batch5.py` and
`tests/c48/spec_batch6.py`. They check preprocessing, exact scope and
conversion rules, pointer operations, scalar/array initializers, and
control-flow semantics using the new SDK. A negative directive test exposed
a lexer error: multiline block comments crossing a preprocessing directive's
physical line were accepted. `sdk/rcc/lex.py` now rejects that source. The
same change correctly restores beginning-of-line state after a multiline
comment outside a directive. An 8-bit negative shift-count assertion was
corrected to the specification's low-three-bit count rule.

The complete independent verifier recorded **806 PASS, 0 FAIL, 0 ERROR** in
both requested backend modes. Exactly **430 of 759** indexed paragraphs have
one or more direct passing assertions; **327 required paragraphs remain
pending**, together with **two explicitly undefined** entries. A linked
assertion is not a complete proof of its paragraph's other obligations.
The regenerated `tests/c48/dispositions.csv` reflects the actual checked
run. The release gate returns 1, as required, because coverage is incomplete.

The private checker passed 491 self-tests and 344223 whole-tree checks before
the final report update; 22 release unit tests passed. SDK host VM regression
passed 73/73 native and 73/73 bytecode sessions. Those are VM tests, not
native hardware or a fresh FUSE boot. The final revision still needs on-target
integration, matched historical image states, LM load/size documentation, and
the mandatory new FUSE ROM boot. No v1 release has been approved.

## Independent checked-ROM floating corpus — 12 October 2026

`tests/c48/spec_batch7.py` records 17 literal-to-five-byte golden
representations, a chained operation with fixed intermediate rounding, and
two independent numeric-error cases. Its reference is the actual verified
48K Spectrum ROM (SHA-256
`d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42`)
executed through the checked Z80 simulator. The test reruns that ROM oracle
and checks its fixed byte results before compiling programs on the new SDK.
It then compares actual runtime storage and error statuses using native and
bytecode backends. This is not a comparison to ordinary IEEE host floats.

The complete verifier now records **850 PASS, 0 FAIL, 0 ERROR**, with **437**
paragraphs linked to specific passing assertions. **320 required**
paragraphs and two explicitly undefined entries remain unexercised.
No Windows C48 implementation has been tested; a real final ZX-UX native
and FUSE integration release gate remains mandatory. No final release is
approved.

## Primary expressions and control-flow batch — 12 October 2026

`tests/c48/spec_batch8.py` adds direct runtime and diagnostic assertions for
C48 primary expressions, excluded expression syntax, executable statement
forms, host-source line conventions, and local quoted include behavior.
The current SDK's native and bytecode backends were both exercised;
acceptance/rejection cases use the compiler's language front end.

The complete specification verifier records **888 PASS, 0 FAIL, 0 ERROR**.
Exactly **461 of 759** indexed specification paragraphs are linked to at
least one passing assertion; **296 required paragraphs** and two explicitly
undefined entries remain without linked checks. Each link supports only its
observed behavior, not every clause of the paragraph. Twenty-two release
unit tests passed, and the private checker passed its self-tests and
complete proposed-tree inspection. The mandatory coverage gate returned
status 1. No final release approval is recorded. The earlier ZX-UX native
and FUSE runs remain checkpoints for the preceding source revision.
