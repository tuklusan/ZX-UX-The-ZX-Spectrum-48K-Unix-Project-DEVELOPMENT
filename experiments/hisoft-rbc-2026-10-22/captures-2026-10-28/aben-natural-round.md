# Aben: native three-wave end prompt (2026-10-29 UTC)

The unchanged published `24-aben.ssx` was run in the original ZX-UX 48K
kernel and Z80 emulator. The keyboard selected the visible alien with `v`,
then released the instruction-screen PAUSE with `a`. After the game's
three traversal cycles, the original BASIC end path (lines 60, 73-74,
305-340) displayed `SCORE:0`, `HI-SCORE:0`, and
`Do you want to see the alien?` on the real framebuffer.

This establishes a natural end-of-round transition at zero score. It does
not establish a successful hit, a nonzero score, INPUT response, replay,
STOP, shell return, or a winning strategy. A separate trial sending `n`
and ENTER did not advance the original INPUT prompt; its behavior remains
unverified. No native code, source, ROM, game memory, or displayed pixels
were changed to produce the capture.

Reproduce on a configured ZX-UX host with the frozen system tape rebuilt
identically at `build/out/ZX-UX.tzx` and the checked 768-byte font recovered
at `build/tmp/rbc-recovered/rbc/font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_ABEN_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
  experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_aben_natural_round.py -v
```

One native test passed without skipping. Loader admission: SSX file **8,721**
bytes; image **7,806**; BSS **598**; stack **384**; total **8,788**, each
required bound below the unchanged **14,000** byte loader limit. The test
checks that original BAS, TZX and SSX bytes are unchanged after execution.

| Original or genuine capture | SHA-256 |
| --- | --- |
| `24-aben.bas` | `ee69ab45dbeaf276ad8483f9d98b963786fbd1841ec2dcd021efd592f74a9c41` |
| `24-aben.tzx` | `1b52599ee52f1a28ee43065a6da16dbdc6656000ef6169d425b5eb4aa8a287c1` |
| `24-aben.ssx` | `69f688884b287615b07a4acc764e1145011c2633350e4331d243717bdfc91906` |
| Frozen ZX-UX system tape | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| Checked printable font | `7b8faa46ee8359ea1cf141a85f618f9f3716334495f3c5c107bb1e5cb86cc468` |
| `aben-three-wave-prompt.png` | `23f7b4191683379783b0b30673274400909189397e12c7c4050947ec4df1701e` |

The PNG came directly from the genuine 6,912-byte Spectrum framebuffer
through `rvm.write_png`. It has not been edited or redrawn.
