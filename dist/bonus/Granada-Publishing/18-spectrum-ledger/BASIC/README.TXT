SPECTRUM LEDGER — GRANADA PUBLISHING

We kept the original SpectrumLedger.tap from the Granada Publishing archive. The original program contains the same 3,085 BASIC program bytes as the recreated TZX. We regenerated 86 numbered BASIC lines using the ZX-UX ROM LLIST converter.

The program runs a five-horse race. The player chooses a horse and enters an amount from the starting 100 units. We chose horse 1 and a stake of 10 during a genuine Fuse 48K run. The race screen showed horses moving across the track. The final view showed a loss of 10 and a remaining balance of 90. These are game credits, not a financial account. We did not start another race.

REPLAY.sh loads the original TAP and repeats the inputs. The pictures came from Fuse rather than the archive. The replay runs Fuse at 400% speed because the opening sound sequence takes a while at 100% speed. No native binary is included.

Original TAP SHA-256: b4ebae36bf0a611539d237601755580d4ef02cec61d543e3d3c5d5b16f638a83
Recreated TZX SHA-256: 0df113ecc2a295469fc0fb4fc9b18593ac64665f1e1b7fe31b0d786b9ba31e10
Regenerated BASIC SHA-256: 66c1b1e7c97d46a3ba54c75e520388efbd0c7684e314553f2f74d5f4f7ebf36d

From the repository root:
  sh src/assets/basic-src/original-sinclair-basic-collections/Granada-Publishing/18-spectrum-ledger/BASIC/REPLAY.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.
