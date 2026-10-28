# Native WordSum: SPACE reveal and 1 replay

The unchanged 40-wordsum.ssx was executed by the actual ZX-UX kernel and Z80 emulator. A no-key control showed `PRESS <SPACE> TO REVEAL THE WORD`. Sending SPACE exposed the original dictionary word `HEARTH` and showed `PRESS <1> FOR ANOTHER WORDSUM`. Pressing 1 cleared the answer and displayed a new puzzle with the SPACE prompt. The first and second puzzle displays differed. This validates reveal and fresh-round behavior, not every answer or random seed.

All three PNGs are unedited images generated from the genuine 6912-byte Spectrum framebuffer. The published game, BAS, TZX, system tape and ZX-UX kernel were not changed.

Rebuild the checked ZX-UX system tape and recover the checked compiler font from Git history before running the test. From the repository root:

```sh
RBC_WORDSUM_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
-p test_native_wordsum_reveal_replay.py -v
```

The recorded key scripts were no keys (1100 frames), `{WAIT 500}{SPACE}` (1100 frames), and `{WAIT 500}{SPACE}{WAIT 350}1` (1900 frames). Each is a distinct real ZX-UX kernel boot with a new native game process. The original `40-wordsum.bas` dictionary is used for the word check.

| Source or output | Bytes | SHA-256 |
| --- | ---: | --- |
| `src/bonus/60-programs/40-wordsum/BASIC/40-wordsum.bas` | 2902 | `5ad48468d44af7faba6be224b8bada73cf618c5668a9659a055fa4a47cc7fa7f` |
| `src/bonus/60-programs/40-wordsum/BASIC/40-wordsum.tzx` | 2788 | `24785370588cd89208b511ce16bc244be5fb8a1c82f9cb02cd3c50319d32043a` |
| `src/bonus/60-programs/40-wordsum/bin/40-wordsum.ssx` | 7692 | `d58f842733846c56cbfc855033b974bebde95534c5657b49f5fc829ebc8f6bae` |
| `experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/wordsum-initial.png` | 2860 | `d84984ef4139d4edb2637a8eba06883e464d28e398af5e14f391aacbf7cabe7a` |
| `experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/wordsum-revealed.png` | 3102 | `47236e53e17c23fd26cb3d48fb2e969f7b2596a99fc34757c71b1abc205c4c83` |
| `experiments/hisoft-rbc-2026-10-22/captures-2026-10-28/wordsum-replayed.png` | 2885 | `244a2f8ab81ef4ffad1b1913a1c10b7751491f85adb8318ec6a2f6707d39096d` |
