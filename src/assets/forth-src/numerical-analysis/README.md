# F83 numerical-analysis corpus

This directory is a local final-delivery test corpus imported from the user
supplied archive `F83_Z80_20_DEMOS.zip`.

Archive SHA-256:

```text
E004302C6CD3A3322F1C1FBB40450A25D771CD5F97AF1AB30949EE6C765C655D
```

## Contents

- `original/F83_Z80_SUITE/` is the extracted archive, retained for provenance.
  It includes the original `.F83` sources, `COMMON.F83`, optional `LINCORE.F83`,
  the `CPM/` line-ending copies, the included host-model tools, checksums, and
  reference outputs.  The archive's generated `tools/__pycache__/` was omitted.
- The twenty lowercase `.fth` files in this directory are the rfc-target
  adaptations that `forthbuild.py` compiles.
- `original/F83_Z80_SUITE/reference/EXPECTED.csv` contains the expected output
  lines.  `HOST_OUTPUT.TXT` is the included constrained-host-model fixture;
  `AUDIT_REPORT.TXT` records the archive's source audit and model run.

The archive reports 20/20 source audits, constrained-model executions,
independent numeric oracles, and host-output comparisons.  Those claims are
evidence about the supplied host model, not evidence of a Z80 execution; this
project adds the independent `rfc` → `ras` → `rld` → `rvm` check.

## Adaptation for rfc

Each target `.fth` file contains, in order:

1. a provenance comment;
2. the contents of `original/F83_Z80_SUITE/COMMON.F83`;
3. `LINCORE.F83` for `minilin`, `lupivot`, and `polyfit`;
4. the corresponding original demo source.

The support sources are concatenated because rfc is a batch compiler and does
not implement the historical interactive `INCLUDE`/`LOAD` workflow.  The
numerical algorithms and expected output tags are otherwise retained.  The
archive's CP/M copies and Python host model are not compiled as target
programs.

The demos use signed 16-bit cells and Q1000 fixed-point arithmetic.  They do
not claim required floating-point support.  They exercise static data, `D+`,
`UM/MOD`, floored `MOD`, nested loops, matrix operations, root finding,
quadrature, ODE integration, relaxation, FFT, and polynomial fitting.

## License status

The project owner has confirmed ownership of these sources.  The archive does
not carry a separate license file; preserve that ownership/provenance note and
the archive checksum when the corpus is moved.  If a public release requires a
standalone license notice, add the owner's chosen project-compatible notice
before publication.

## Expected outputs

The expected fixture has one or more lines per program.  Output comparison is
token/value based rather than whitespace based because Forth numeric formatting
may vary.  The canonical program tags are:

```text
WHET, MACHAR, LCG, SQUARE, MINILIN, GEMM, LUPIVOT, THOMAS,
CHOLESKY, BRENT, NEWTON, BISECT, ROMBERG, SIMPSON, GAUSS,
RK4, EULER, JACOBI, FFT, POLYFIT
```

The archive's exact lines are in `original/F83_Z80_SUITE/reference/EXPECTED.csv`.
