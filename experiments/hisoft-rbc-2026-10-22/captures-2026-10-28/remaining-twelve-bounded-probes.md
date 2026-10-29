# Twelve published programs: bounded native investigation (2026-10-29 UTC)

The two reproducible runs below used **ten isolated ZX-UX loader/Z80 emulator processes concurrently**, then the other two in a second batch. Each worker loaded its own unchanged original published SSX, checked both native 14,000-byte admission limits, compared the frozen ZX-UX tape, observed authentic 6,912-byte Spectrum screen memory, and rechecked the original BAS, TZX, SSX and ROM file bytes after execution. No game source, executable, emulator, kernel, RAM values or pixels were edited. A probe completing is **not** a claim that its game completed a round.

Execute from the repository root with the checked ROM, original system tape at `build/out/ZX-UX.tzx` and the checked 768-byte font at `build/tmp/rbc-recovered/rbc/font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  experiments/hisoft-rbc-2026-10-22/tests/probe_native_remaining_batch.py \
  --batch ten --jobs 10 --frame-cap 1500 --child-timeout 100 \
  --output build/tmp/remaining-batch-ten.json
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  experiments/hisoft-rbc-2026-10-22/tests/probe_native_remaining_batch.py \
  --batch two --jobs 2 --frame-cap 1800 --child-timeout 100 \
  --output build/tmp/remaining-batch-two.json
```

Both batches returned observations for all 12, without a worker error. The output JSON retains exact keyboard scripts, individual original SHA-256 hashes, loader sizes, sampled text, screen SHA-256 hashes, process state, and the fact that no complete round or exit was established by these bounded runs. Outputs remain untracked under `build/tmp/`; the runnable probe source is checked in here for repetition.

| Program | Bounded observation; **not** a complete-game result |
| --- | --- |
| Critical Path Analysis | Network demonstration and explanation advanced; process still marked live, but did not own the screen at the end of the sample |
| Battleships | Instruction screen and skill-level entry; no fleet destroyed |
| Tanx | Reached player 2's elevation prompt after earlier input; no seven-point game-over |
| Paypackets | Reached cash-amount input, with zero total; no completed payment |
| Newmarket | Advanced instruction pages; no completed horse race |
| Dam Busters | Native game score display at zero; no final defeat or score result |
| Dogfight | Displayed player lives 1 and computer lives 2; no round ending, screen ownership absent at final sample |
| Exocet | Three missiles consumed (EXOS:7, SCORE:0); no completed missile supply or game-over, screen ownership absent at final sample |
| Roots | Numerical introduction progressed; a **separate** focused test and authentic PNG already prove one complete `25` square-root calculation, not STOP |
| Bulls and Cows | Reached guessing-count INPUT; no four-digit evaluation or final answer |
| Tug of War | Native process ran without decoded text in the bounded sample; screen ownership absent at final sample, no win |
| Mushroom Invasion | Instruction screen and later graphical display; no destruction or score proven |

All 12 stayed without a recorded foreground-process exit at these bounded checkpoints. **Screen ownership was not retained** at the final sampled frame for Critical Path Analysis, Dogfight, Exocet and Tug of War; this deserves a separate safety/isolation investigation, not a silent pass. No victory, replay or STOP is inferred from a mere screen change. Earlier longer Exocet and Dogfight trials likewise did not establish an ending. For the complete Roots calculation, see `roots-custom-square-round.md` and `roots-25-square-calculated.png`.

Batches were intentionally capped to preserve repeatability; they do not disprove behaviors requiring more time or different keys. After the separately verified Roots calculation, **11 games** still lack a proven end-of-round or equivalent complete user task. The other 23 have some documented complete task, losing-round, scoring or restart outcome, not exhaustive control and victory coverage. Published totals remain **120 originals, 34 SSX and 26 README**; this investigation does not alter any game outcome files.
