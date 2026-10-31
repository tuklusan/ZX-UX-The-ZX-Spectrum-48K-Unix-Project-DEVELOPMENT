# Spectrum 60: BASIC source from the original TZX tapes

The 60 programs under `src/assets/basic-src/original-sinclair-basic-collections/60-programs/<game>/BASIC/` contain
an original `.tzx` tape and a regenerated, numbered ASCII `.bas` listing.
The TZX is the source for the current BAS text. The BAS files were updated
on 24 October 2026 by running the standalone
`build/tools/zx-tzx2bas.py` converter on each matching TZX file.

The converter reproduces the original ZX Spectrum 48K ROM LLIST character
formatting, including its built-in keyword table and token-spacing rules.
The original token bytes are read directly from each TZX. The converter
skips the five-byte numeric values stored after visible BASIC numbers.
It writes `{HH}` escapes where an ASCII listing cannot safely express a
Spectrum character byte. The listings are intended for human reading and
further translation; the original TZX remains the reference for exact
loaded program bytes and cassette operation.

## Repeat the conversion into a new directory

From the ZX-UX repository root:

```sh
python3 build/tools/zx-tzx2bas.py \
  --corpus src/assets/basic-src/original-sinclair-basic-collections/60-programs \
  --out-dir build/tmp/tzx-basic-listings
```

For one tape:

```sh
python3 build/tools/zx-tzx2bas.py \
  src/assets/basic-src/original-sinclair-basic-collections/60-programs/01-minelay/BASIC/01-minelay.tzx \
  -o build/tmp/01-minelay.bas
```

The tool refuses to replace existing output files or to write directly
into any preserved game `BASIC/` directory. Running the tool does not change the checked-in BAS files.

A readable BASIC listing does not guarantee that another compiler accepts it.
