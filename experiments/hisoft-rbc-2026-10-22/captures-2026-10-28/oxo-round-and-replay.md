# Native OXO: complete round, score and new game (28 October 2026)

These are authentic `rvm.py` ZX-UX loader/Z80 framebuffer captures of the **unchanged, published** `src/bonus/60-programs/29-oxo/bin/29-oxo.ssx`. Original BAS/TZX were not modified. This is one real game round, not proof of all possible moves or all 34 games.

- `oxo-completed-round.png`: original program displayed **I WIN**, **Score: You 0   Me 3    Draw 0**, and **Press any key for new game**.
- `oxo-replay.png`: a follow-up key displayed a fresh board with **Me to go FIRST**.
- `tests/test_native_oxo_complete_round.py`: automated real-kernel assertions of the same two screens, real process state, native header and unchanged source bytes.

From repository root, with the checked kernel tape built locally:

```sh
keys='{WAIT 250}'$(printf '123456789123456789' | sed 's/./&{WAIT 45}/g;s/{WAIT 45}$//')
python -B src/zx-ux-sdk/rvm.py src/bonus/60-programs/29-oxo/bin/29-oxo.ssx \
  --system build/out/ZX-UX.tzx --frames 2400 --keys "$keys" \
  --png experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/oxo-completed-round.png --headless
python -B src/zx-ux-sdk/rvm.py src/bonus/60-programs/29-oxo/bin/29-oxo.ssx \
  --system build/out/ZX-UX.tzx --frames 3600 --keys "${keys}{WAIT 1650}a" \
  --png experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/oxo-replay.png --headless
python -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_oxo_complete_round.py -v
```

SHA-256:

```
BAS  3664d4780d49ea51a738806630549f20b85c4c02e0832da45e5e6ef63908fd64
TZX  05b38650cd39dde101d00854d7e69e390fb09f7076b3625dc2ea99a2c899bd7e
SSX  21c391afe9529203f7108e512b571b510c19c95fe3a914d4f5bf7e57d2e1a540
WIN  e2ef2345d3b4890b3cbd7f6e74e0d6d2281731031a9bd140139fbe533878b6e0
NEXT bd335106d7b4a8135b1e177f313ed878d9470fe20246e570254e54a3a0f9565b
```
