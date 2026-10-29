# Motocross: native obstacle crash and menu retry (2026-10-29 UTC)

The original published `06-motocross.ssx` ran in the real ZX-UX 48K
loader and Z80 emulator. At the title/menu, keyboard `1` selected the
Moto-cross race. No jump was attempted. The original BASIC line 1030
reported `Bad Luck! You crashed.` and displayed the game-selection menu.
A second genuine `1` selected another run. The crash/menu disappeared,
the course was drawn again, and a second obstacle crash returned to the
menu. The same process retained screen ownership. This proves a losing
race and a replay, not the stunt-cycle course, a successful finish,
full gameplay coverage, or menu option `3`/STOP and shell restoration.

Reproduce with the frozen tape at `build/out/ZX-UX.tzx`, matching
`build/out/kernel.json`, and the checked 768-byte font in
`build/tmp/rbc-recovered/rbc/font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_MOTOCROSS_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
experiments/hisoft-rbc-2026-10-22/tests -p test_native_motocross_crash_replay.py -v
```

Original BAS SHA-256: `e41da2b40fb5ea332ca0375a865a782191a4ab63f683c75203ae6d5bb75ac820`.
Original TZX SHA-256: `119f29f00c0caee152254f0578dabaa04511d12dffffe4f354d4431643d7f7ad`.
Published SSX SHA-256: `cfb276a62daabb71dd5933243a29056bf15a862c672a3b48d93b2e8d3eb68937`.
Frozen tape SHA-256: `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597`.

Unmodified ZX-UX framebuffer captures from `rvm.write_png`:

- `motocross-crashed.png`: SHA-256 `085d38dc18d1f056518743d2636a1818b7040e8f1b31864256fae24257c24008`.
- `motocross-restarted.png`: SHA-256 `7c2120f51ad349dfc8825a74a5e25501048a8bfbbccb5f7349328e2c93a19246`.

No game BAS, TZX, SSX, ROM, or system tape bytes were changed.
