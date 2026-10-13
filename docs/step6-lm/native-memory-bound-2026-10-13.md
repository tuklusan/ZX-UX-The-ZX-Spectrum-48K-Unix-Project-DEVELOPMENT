# ZX-UX v1: LM memory observations

The approved current SDK compiled `programs/c48/ailmzx48/ailmzx48.c` to an SSX1 native image of 17,870 bytes. It requires 21,151 bytes under the actual loader calculation. The configured SDK memory allowance is 14,000 bytes. The ROM-loaded candidate ZX-UX 48K snapshot reported 10,322 bytes free before the attempt.

Running the LM program name through `/dev/cassette/ailmzx48` produced the kernel message `not enough memory` at frame 263. Free memory was 10,322 bytes after the refused load. The program did not run. The result is the expected memory-limit exception and is **not** a substitute for execution of LM.

The test script `tests/lm_native_memory.py` records loader behavior, memory counts, and screen captures.
The snapshot was built from an individually checked source subset. The complete source checkout requirement remains open.

| Item | SHA-256 |
| --- | --- |
| LM native SSX1 | `80eceb599719fbbade94c70563e1734611c59c8ae6ecb0ae8916b358e6baf39e` |
| Candidate boot TZX | `27471d1d37222ac77194fc1a08dfef4bd080dcfafd682c6d3148101d6ee4b95b` |
| Tape-derived snapshot | `d804a824bd16bbf3470ff0b1fbdf983400fd027cedcbacbd17c8a61e1a82d4e3` |
| ROM | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| Screen RAM `.scr` | `37963d69fb3ac3f910a479e8e8418fe11f92e7add1069615d787a775988a6602` |
| Rendered PNG | `506d1b418d9000943b2cb4c5361e84c013d4e8c672559fa184cf8cf9ef6a7998` |

The native LM execution requirement remains **unproven**. The user's new-SDK-only waiver excludes rerunning LM with the historical SDK, not the obligation to label the v1 memory bound correctly. Final build, integration, C48 and real FUSE release checks remain open.
