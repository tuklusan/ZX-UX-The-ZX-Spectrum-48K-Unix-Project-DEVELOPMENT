# Native INPUT editor: authentic, experimental ZX-UX framebuffer captures

These three images were **captured from actual ZX-UX/Z80 runs** of original,
numbered BAS game listings. Each candidate was assembled from separately
three-base-verified HiSoft pre-link Z80 source using `ras` and `rld`. A
source-owned experimental editor replaces one ROM editor call *before
assembly*. The published 34 game SSX files, all 120 BAS/TZX originals,
ZX-UX kernel and frozen system tape remain unchanged. **The experimental
editor is not installed into RBC, is not published as a game SSX and has
not passed full memory bounds, erroneous-input or gameplay safety checks.**

Verified outputs on 2026-10-28, reproduced with `reproduce.py`:

| Original game | Observed original-game behavior | Screenshot SHA-256 | Experimental SSX SHA-256 | File/image/BSS/stack/total bytes |
| --- | --- | --- | --- | --- |
| 23-biorhythms | Entered six dates; physical-cycle graph with `28/10/2026+` | `01e92917e574f3653dd42a6ec8727ffb4ceb043a9ddcfe24865ec3dae275a2e8` | `813ced39b76efe2d0e8454afbf44a1c0dba2c03232ce58e49cd65f9e5f40dcc0` | 8,364 / 7,476 / 160 / 384 / 8,020 |
| 56-roots | Entered three prompts; original root-of-25 demonstration appeared, stopped at next INPUT | `2fe7cfd49948f034fc259acc07cc8517a99e0d4c472e464cbfd68ae3838c1078` | `ea9efc429a1ca6a9717ee885e331d240534847e17b777e3ae6199e6a41540afc` | 11,108 / 10,092 / 835 / 384 / 11,311 |
| 07-critical-path-analysis | Proceeded past instructions and original DATA checksum into network diagram; stopped at `finish node` prompt | `0a939cad5043a003278af42b6845d832e149a904cdeb860aafb6f4775b824115` | `8bfdf1a2628e851278ae6ecd2943aa4290131ec45707b37071020f025ddf680c` | 11,709 / 10,307 / 2,885 / 384 / 13,576 |

Reproduce from the repository root, after building the checked RBC frontend
and ZX-UX tape. Set `RBC_FRONTEND_DIR` to the checked upstream frontend and
`RBC_HISOFT_TAPE` to the checked, reconstructed HiSoft tape. All screenshots
are genuine emulator outputs. Each command starts a **fresh Python process**
to isolate original HiSoft global state:

```sh
python3 experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/input-bridge-experimental/reproduce.py 23-biorhythms --output experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/input-bridge-experimental/23-biorhythms.png
python3 experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/input-bridge-experimental/reproduce.py 56-roots --output experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/input-bridge-experimental/56-roots.png
python3 experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/input-bridge-experimental/reproduce.py 07-critical-path-analysis --output experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/input-bridge-experimental/07-critical-path-analysis.png
```

The script records the original BAS/SSX, experimental SSX, framebuffer, and
PNG hashes, plus measured native memory sizes. It rejects outputs outside
the experiment/build area. It explicitly verifies the rebuilt and frozen
ZX-UX system tapes are byte-identical. A screenshot is a bounded game-flow
observation, **not** proof of a completed level, correct final answer,
portable production INPUT behavior, or gameplay validation for 34 games.
