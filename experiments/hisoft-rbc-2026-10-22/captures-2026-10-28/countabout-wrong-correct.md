# Native Countabout: wrong answer, correct answer, next prompt

Authentic ZX-UX 48K Z80 framebuffer PNGs, 28 October 2026. No process
memory, game listing, linked SSX, or pixels were edited. This is one
complete five-flower answer and another prompt, not full coverage of all
Countabout questions or the other 33 published games.

The unmodified `60-countabout.ssx` starts through the original kernel.
After the two opening keys, the original game displays five flowers.
A physical `9` key displays **N O,W R O N G A N S W E R !** and returns
to the question. A physical `5` displays **C O R R E C T** and
**5 F L O W E R S**, then advances to **PLEASE PRESS ANY KEY**.

- `countabout-wrong.png`: real wrong-answer display.
- `countabout-correct.png`: the game's correct-answer screen.
- `countabout-next.png`: the next question prompt.
- `tests/test_native_countabout_round.py`: repeatable framebuffer,
  memory-admission, source-preservation and process checks.

From the repository root, with `build/out/ZX-UX.tzx` rebuilt and byte-identical
to `dist/zx-ux/tzx/ZX-UX.tzx`, and the 768-byte original font recovered:

```sh
RBC_COUNTABOUT_CAPTURE_DIR="$PWD/experiments/hisoft-rbc-2026-10-22/captures-2026-10-28" \
  python -B -m unittest discover \
    -s experiments/hisoft-rbc-2026-10-22/tests \
    -p test_native_countabout_round.py -v
sha256sum experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/countabout-*.png
```

SHA-256:

```text
BAS       2147bc9a6aed314075e9257eca9c671d7de922b051fb36e6e8faf82dc7703294
TZX       2e947f6969b718df6f308d1254ce9320811e4129712433f6314f62d068453b8b
SSX       690d42a7130cdeb15c210039743d86d8f5f924e81dc7c2ff2c85162ff2ca16b7
WRONG     a56df7c77329aac6a878d76058c6ceed7926ede6382228389d11c90e285e8310
CORRECT   03ef54bbd3feb759462b916f8a071b5da5ecc53e066a7fb56fe2c0c876e9d4b8
NEXT      f26ccd5eccf3fd0f9a8a152d75989d205127df7aa4ab431da34892257e8d1db9
```
