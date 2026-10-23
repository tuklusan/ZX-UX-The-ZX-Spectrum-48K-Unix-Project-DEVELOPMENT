# RBC original BASIC failure groups — October 23, 2026

This is an analysis of the saved five-shard run `39878801410`, compiled at
source commit `5a5e0ee2ec1b77c4fa49fa3f0361e7718d87d6d9`. Its permanent
input records are in
`experiments/hisoft-rbc-2026-10-22/rbc-run-39878801410-results.zip`.
The ZIP SHA-256 is
`3d5b45ae2c09f3346bb19792b76ea74353a2d799ce50db38463d01c587b5445c`.
The saved source is older than current development main. The numbers below
are a baseline, not results from the newer native PAUSE and parser changes.

The 121 input records contain 16 successful compilations and 105 failures.
The 105 failures break down as follows:

| First detected failure cause | Input count |
| --- | ---: |
| Memory-access safety stop | 72 |
| Other unsupported compiler operations or number syntax | 18 |
| Spectrum character conversion error | 9 |
| Computed BASIC line number | 5 |
| BASIC text line parser | 1 |

Within the 72 memory safety stops: 41 global writes, 20 unbounded writes,
7 global reads, and 4 tape or other external loading operations. These
counts refer to the first reported blocking operation for each input; they
are not a scan of every operation that a program might execute.

The latest compiler source handles some previously reported failures, so
none of the earlier failures should be assumed unresolved without rerunning.
The correct next batch is to run fresh input tests, examine the 72 memory
cases by precise address and intended action, then repair only safe compiler
or runtime mappings. Never relax the strict memory stop just to raise a count.

Result collection now has FAST, BATCH, and FULL modes. The FULL mode is the
only compilation coverage claim for all 121 inputs. An accepted C48 port
never counts as a pass for this separate compiler track. Program completion
also requires the defined native gameplay and display checks.