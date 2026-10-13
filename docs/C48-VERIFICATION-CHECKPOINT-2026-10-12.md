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
executed through the checked Z80 simulator. The test reruns that ROM reference
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

## Host compiler command and output contract — 12 October 2026

The current SDK command driver had two reproducible contract defects:
`-o` could target its own source file and overwrite it with a compiled
image, and an option missing its value could emit a Python traceback.
`sdk/rcc/driver.py` now checks output aliases, including links, before
writing; it also validates numeric option values and conflicting mode flags.
Output write errors receive a nonzero status and a host diagnostic.

`tests/c48/spec_batch9.py` adds 17 direct host subprocess cases covering
assembly, SSO1 and SSX1 output, default and explicit filenames, source
retention, invalid command use, and error status behavior. The release
independence check now tests the output signature and source guard without
relying on the former literal implementation spelling.

The complete independent C48 verifier records **905 PASS, 0 FAIL, 0 ERROR**.
There are **476 paragraphs with linked passing assertions**, **281 required
paragraphs pending**, and **two explicitly undefined entries**. Both SDK
host-runtime modes passed their complete 73-session suites; 22 release unit
checks passed. The C48 coverage gate returned status 1. The current
source has no final release approval.


## Multiscalar ABI regression — 12 October 2026

The specification-led verifier now includes `tests/c48/spec_batch10.py`:
conversion, evaluation order, stack argument passing, multiple float
parameters, a recursive IX frame, and rejection of unsupported calling
convention keywords. An observed native compiler defect caused a
nonrecursive float callee to overwrite its saved return-address register
while copying an earlier float argument. `sdk/rcc/z80gen.py` now protects
the saved return address across that copy. Separate tests exercise two
and three float arguments, mixed scalar/float parameters, and recursion.

The checked 48K ROM's decimal parser does not produce the canonical exact
binary-half bytes for text `0.5`. The mixed-conversion test therefore
compares against runtime `1.0/2.0`, instead of assuming decimal parsing
and arithmetic produce identical encodings for the same mathematical value.
The numeric behavior and ROM conversion remain unchanged.

Complete C48 verifier (both output modes): **937 PASS, 0 FAIL, 0 ERROR**.
**492 of 759** paragraphs have linked assertions, **265 required**
paragraphs lack linked tests. The other two entries are undefined.
The required coverage gate still exits with status 1. No v1 release has
been approved; newly built system images and visual alignment still need
the final clean-release gate.


## Additional C48 direct tests — 12 October 2026

The updated SDK records 978 passing executions across both compiler
backends, zero failures, and zero errors. The verified tests link
516 of the 759 indexed specification paragraphs. Another 241 required
paragraphs remain pending and two have explicitly undefined behavior.

The new `tests/c48/spec_batch11.py` checks source syntax, initialization,
pointer comparisons, pointer differences within an array, numeric results,
argument passing, and repeated compiler output. A defect in pointer
comparison checking was repaired in `sdk/rcc/parse.py`, so unsupported
relational comparisons involving `void *` now fail compilation.

The updated tests and ledger cover only their observed results. They
do not establish every obligation in a paragraph. Both host runtime
suites passed 73 sessions each; the 22 release unit tests passed.
The full release remains blocked by the incomplete required-language
coverage and historical visual comparison work.



## More C48 conformance checks — 12 October 2026

The updated SDK records 1022 passing executions across both compiler
backends, zero failures, and zero errors. The verified tests link
537 of the 759 indexed specification paragraphs. Another 220 required
paragraphs remain pending and two have explicitly undefined behavior.

The new spec_batch12.py checks source values, memory layouts, calling
behavior and error status. All 22 release unit tests passed. The
full release remains blocked by incomplete required-language coverage
and historical visual comparison work.

## Batch disposition of the original 220 pending paragraphs

The current new-SDK verifier records **1,122 PASS, 0 FAIL, 0 ERROR** in
its two execution modes. **645 of 759** indexed paragraphs have direct
passing assertions. **112 required** paragraphs remain without linked
proof, alongside two entries expressly classified as undefined.

The audited set is the exact **220 required paragraphs** outstanding in
the earlier 1,022-execution checkpoint. The checked clause inventory in
`tests/c48/original_220_dispositions.csv` records each outcome:

| Review outcome | Number |
| --- | ---: |
| Newly linked to a passing assertion | 108 |
| Documentation, contract policy, or verification-process requirements | 54 |
| Requires genuinely independent host/cross-system validation | 34 |
| Requires further target/runtime, ABI, or format proof | 20 |
| Broad compiler-corpus requirements still incomplete | 2 |
| Outside defined portable pointer behavior | 1 |
| Optional internal implementation method | 1 |
| **Total** | **220** |

A disposition is not a waiver, a compiler pass, or a reclassification of
specification requirements. The 112 remaining required clauses are still
reported by the unmodified mandatory coverage gate. The suite's new
`spec_batch13.py` contains direct compiler/runtime/format checks; the
`spec_batch14_audit.py` entries only pass when the exact identified
constituent compiler tests pass, including both runtime modes where
applicable. An audit confirms the checked examples, not all behavior
in a broad paragraph.

The new format probes parse actual SSO1 symbols, check the SSX1 20-byte
header and checksum rejection, and check the SST1 cassette data against
the compiler-generated executable. A generated-code probe checks that
its tested native output does not use IY. These are narrow observations,
not a complete ABI proof. No historical format adapter was introduced.

To regenerate the language report, the original-220 inventory, and the
full release gate result from the checked SDK toolbox:

```
python3 tests/c48/conformance.py --backend both --report build/logs/c48-conformance.json
python3 tests/c48/review_original_220.py --report build/logs/c48-conformance.json --output tests/c48/original_220_dispositions.csv
python3 tests/c48/dispositions.py --run build/logs/c48-conformance.json --output tests/c48/dispositions.csv
python3 tests/c48/coverage_gate.py --report build/logs/c48-conformance.json
```

The release coverage command remains nonzero while requirements lack
proof. An additional implementation and previous runtime captures need
separate verification. Output modes from this SDK do not replace it.
Final native integration and clean FUSE release approval must use a fresh
exact-current-revision checkout. This source milestone is not a release.

## Canonical source comment-byte clarification

The specification's source-representation paragraphs 39, 42, 44, the
code listing in paragraph 45, and paragraph 49 now explicitly permit
any byte inside `//` or `/* ... */` comments. An LF still terminates
a physical line, and the normal rules for comment termination apply.
Outside comments, the canonical ASCII source restrictions remain in
force; non-ASCII language tokens and literal contents are not admitted.
This accommodates, for example, copyright symbols in UTF-8 comments.

The updated document and traceability file carry a new source hash.
The direct comment-byte fixtures run in both compiler modes, including
positive high-byte, control-byte and UTF-8 comment cases and negative
outside-comment cases. The full verifier records **1146 PASS, zero FAIL,
zero ERROR**. There are **647 linked paragraphs, 110 required pending,
and two explicitly undefined entries**. The scoped host-compiler gate
passes under the approved `rcc` architecture interpretation; the full
release gate still stops on 110 required paragraphs. The separate target
ABI matrix distinguishes 15 supported entries, 3 recorded contracts,
and 2 partial entries; no new target execution is implied here.
