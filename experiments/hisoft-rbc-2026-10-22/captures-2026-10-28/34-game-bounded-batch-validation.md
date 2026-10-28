# 34-game bounded ZX-UX keyboard validation — 2026-10-28

The unchanged 34 published native SSX programs were each run twice in the real
ZX-UX 48K Z80 emulator: once without scripted keys, once with the source-guided
keyboard script. Fresh emulator boots, the frozen ZX-UX tape, and the identical
frame limit were used for each pair. No game, ROM, tape or SSX was modified.

Seven groups of at most five independent checks completed on the local runner.
**34/34 completed; 27 framebuffer differences; 7 unchanged; 0 process errors or
per-game timeouts.** The broad screen check intentionally fails on seven
unverified input effects. A changed framebuffer is not full gameplay proof.

The new runner defaults to five parallel jobs, groups of five, and **2,400
seconds (40 minutes) per game**. It saves raw stdout, stderr, exit code and
classification for each game in a unique untracked `build/tmp` run directory.
A timed-out game remains unverified, and its partial output is kept.
Sequential groups continue even if a checked game is unchanged.

The seven current broad-gate unresolved games split into two sets:

- Five games whose original program uses `INPUT`: Minelay, Critical Path
  Analysis, Biorhythms, Space Traffic and Roots. Their source-level raw editor
  checks are experimental; the shipped INPUT path is not fixed.
- Two games with mistimed broad keyboard scripts: Scuba and Swordsman.
  Separate source-guided real-emulator tests already show Scuba reaching its
  underwater screen and Swordsman advancing after the replay key.

Flying Geese shows a difference in this broad check. That does **not** verify
ENTER replay in the published game. Only the test-only editor replay has been
observed. Production INPUT and complete game coverage remain unresolved.

## Local raw outputs

The following seven command transcripts are untracked under `build/tmp`.
Each points to the untracked directory containing all individual game logs.
SHA-256 values verify the output bytes produced in these runs.

| Group | Games | SHA-256 of batch stdout |
| --- | ---: | --- |
| 01 (`build/tmp/rbc-gameplay-34-batch01.log`) | 5 | `7e827b6e2373fb19b13fc9abb0a0186e6d2dc1d5d6232a19881333b30582b024` |
| 02 (`build/tmp/rbc-gameplay-34-batch02.log`) | 5 | `2aa451656fceeeebba43820fc43facc2532e7048754a602f0e055c1f20ddad9f` |
| 03 (`build/tmp/rbc-gameplay-34-batch03.log`) | 5 | `0eba9753435621f7f4f851cf2818d3dff21f2eb17db1f742e06d7fd61c67d578` |
| 04 (`build/tmp/rbc-gameplay-34-batch04.log`) | 5 | `ad8230f0855a8691713d55c7808ab228867d155d1848ce8d85844198003db6d8` |
| 05 (`build/tmp/rbc-gameplay-34-batch05.log`) | 5 | `51470fd71b27668eec28e7cc367c89ac680da545a8ab65d078b8642e8c5330da` |
| 06 (`build/tmp/rbc-gameplay-34-batch06.log`) | 5 | `804657f7472316eba755181574519b6599b133e418c7966058621f798f6cdc4d` |
| 07 (`build/tmp/rbc-gameplay-34-batch07.log`) | 4 | `59f41000131d6836dbb7a6156c7700910339792a4fb4b07dd62832b6f406d8ed` |

Run the full gate on a capable machine or runner with:

```sh
python3 -B experiments/hisoft-rbc-2026-10-22/tests/native_gameplay_batch.py
```

An individual group may be run by listing exact game directory names after the
command. There is no project GitHub Actions workflow dedicated to RBC, and no
workflow was added. The external tool invocation of the all-34 command was
interrupted during its second group; the seven smaller group invocations
finished and provide the complete 34-game result set above.
