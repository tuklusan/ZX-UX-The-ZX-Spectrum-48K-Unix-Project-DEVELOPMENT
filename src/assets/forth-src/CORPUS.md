# rfc program corpus

Included sources must have a permissive licence recorded here.  `reference/`
sources are investigation material only; do not ship code from an entry marked
`reference-only`.

| Program | Upstream source | Authors | Licence | Status |
| --- | --- | --- | --- | --- |
| F83 calendar | [janaite/forth83-80](https://github.com/janaite/forth83-80) `clock.blk` | F83 contributors | Unlicense / public domain | `ported`: CP/M clock I/O is replaced by explicit date arguments in `portable/calendar.fth`. |
| F83 Huffman | [janaite/forth83-80](https://github.com/janaite/forth83-80) `huffman.blk` | F83 contributors | Unlicense / public domain | `port`: `ported/hufdemo.fth` keeps the bit codec, uses target memory instead of CP/M files, and uses a compact fixed codebook. |
| F83 BASIC | [janaite/forth83-80](https://github.com/janaite/forth83-80) `basic.blk` | F83 contributors | Unlicense / public domain | `research`: retained until vocabularies, immediate words, and a resident interpreter are available. |
| Worms? | [savetz/worms](https://github.com/savetz/worms) | David S. Maynard / Kay Savetz | MIT | `port`: `ported/worms.fth` retains the movement loop and replaces 6502 display, sound, and keyboard code with a ZX-UX console board. |
| VolksForth samples | [cstrotm/VolksForth](https://github.com/cstrotm/VolksForth) | VolksForth contributors | BSD-3-Clause | `research`: inspect each selected file before copying; current tree is platform-oriented. |
| pForth benchmark | [philburk/pforth](https://github.com/philburk/pforth) `fth/bench.fth` | Phil Burk and contributors | ISC | `adopt`: portable `sum.cells` and `factorial` are in `portable/pfbench.fth`; host timing loops and other ANS-only benchmarks are excluded. |
| pForth sieve | [philburk/pforth](https://github.com/philburk/pforth) `fth/siev.fth` | Phil Burk and contributors | ISC | `port`: algorithm is in `portable/pfsieve.fth`; the 8190-byte host benchmark table is reduced to 1024 bytes for the ZX-UX arena. |
| F83 numerical-analysis suite | User-supplied `F83_Z80_20_DEMOS.zip` | Project owner | Ownership confirmed by project owner | `adopt`: 20 fixed-point numerical-analysis demos are adapted into `numerical-analysis/*.fth`; support words are concatenated because rfc has no `INCLUDE`. |

Every included program has a nearby README stating its source, licence, target
behaviour, and the changes made for rfc.
