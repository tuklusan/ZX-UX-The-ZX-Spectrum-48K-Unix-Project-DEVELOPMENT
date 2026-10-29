# Production INPUT + 34-game real-emulator regression — 2026-10-28/29

The original 60 BAS and 60 TZX byte hashes were checked before and after.
All 34 game bins use independently source-checked, native ras/rld-linked SSX.
The six INPUT games listed below were rebuilt independently from original
BAS and separately decoded TZX, compared byte-for-byte, and checked at three
relocation bases. No original BAS/TZX, ZX-UX ROM, kernel or system tape changed.

**Published game keyboard regression:** 34/34 separate real ZX-UX emulator
paired boots completed in three independent 12/12/10-game runner invocations;
**34 screen responses, 0 unchanged, 0 errors, 0 per-game timeouts**.
The old six-ROM-INPUT program set yielded 29 screen responses, five unchanged
INPUT cases; the post-rebuild published set yielded 34 screen responses.
**A changed framebuffer does not prove full gameplay, wins, losses, or safety.**

## Exact runner limits and recovery

- Whole invocation: `--runner-timeout 7200` (120 minutes).
- Single game: `--timeout 300` (5 minutes).
- Parallel jobs/group size: `--jobs 12 --batch-size 12`.
- Save stdout/stderr/return code, elapsed time, reason and SHA-256 to
  untracked `build/tmp/` for each game; nonzero unverified gates are retained.
- Run three *separate* invocations, not one 34-game external tool call.

To reproduce from the published sources on a configured ZX-UX host:

```sh
mapfile -t games < <(find src/bonus/60-programs -path "*/bin/*.ssx" -printf "%h\n" | sed "s@.*/60-programs/\([^/]*\)/bin@\1@" | sort -u)
test "${#games[@]}" -eq 34 || exit 1
gate=experiments/hisoft-rbc-2026-10-22/tests/native_gameplay_batch.py
for start in 0 12 24; do
  python3 -B "$gate" --jobs 12 --batch-size 12 --timeout 300 --runner-timeout 7200 \
    --results-dir build/tmp/rbc-gameplay-34-published "${games[@]:start:12}"
  rc=$?; echo "batch_start=$start exit=$rc"
done
```

## Recorded published-binary batches

| Batch | Games | Runner exit | SHA-256 of batch stdout |
| --- | ---: | ---: | --- |
| 01 | 12 | 0 | `1f0a49768ef6e2db2bbba7cb467bf4b590cec8445d24002a2477eb48ba289b2c` |
| 02 | 12 | 0 | `993c2237df2f06c1981f0b349263f16d40c2d7319257c2ede1b9da30ca623da8` |
| 03 | 10 | 0 | `da49bfe6f09a865141a5bd2a990b56af5709dedcf0411aebc963a84d407173d4` |

## Exact per-game classifications

Classification is limited to paired-screen response; no entry below claims
a full game win or loss merely from a screen hash.

| Published game | Prior ROM-INPUT path | Current production | Per-game log SHA-256 |
| --- | --- | --- | --- |
| 01-minelay | BEHAVIOR UNVERIFIED — no input screen change | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `79370ec8eea5e9327babc2c2cf2b94f299c499c6eaf318dfb3903facb1ddf45e` |
| 03-tug-of-war | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `9286745f025df930d85bae0bc7fbfeab313c147f0f6a87eb2af6d083f8cb7c67` |
| 06-motocross | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `fdd881d84298f7d68d5e4249b71d79437797858d9117046edd2277a3b23539de` |
| 07-critical-path-analysis | BEHAVIOR UNVERIFIED — no input screen change | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `3f4be16c59a476456ea11871478b1b6c87a650fad1d75c30a78b5a58fdda7fcf` |
| 09-battleships | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `ad49cfd717355617f859e76df5a7bd069b68574661e11e0eccbb79187cf68bdf` |
| 10-tanx | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `95b2cda423cbfb23f8adaaabf54831c74c10ecba51131af815818db6218a0e01` |
| 12-flying-bomb | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `6097561d890ccc3573c926f973605c997695ff74be3ff3fadb16952d20ecf890` |
| 14-scuba | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `cb290c432cab1f17b20f02d927cce282add1df6c8453cf1475be2f16ab45e2ca` |
| 16-snap | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `b99484a88263dfee38910a3259af70592d1f7e9067173ab9ba535beffb7191bb` |
| 17-paypackets | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `1f7e79548fde3c3644606777aef6b5bc7972a3f2ba193048c9b5a9368639d987` |
| 18-newmarket | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `0db8acc42e6bf1cd65b1e0c46fd1e4e951a54989f411c9b1f84e719a10557b01` |
| 23-biorhythms | BEHAVIOR UNVERIFIED — no input screen change | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `9e8bfbced28403a99b5680ea5d6b2a83b36b35775eec67242b621d11d3c5e46d` |
| 24-aben | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `3918eba81b9995f24ffb77cd12012b88de3efa7f20ee72fd2d6d9e6ccd25853c` |
| 25-galaxians | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `d28b7ff9bbad5590fbac84651bf1b5b4f5e45e1b6a80d7be51d58ff29dd432a9` |
| 28-dam-busters | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `1fbdd508efb80cce30e39e55d5ae4bed922c9e174f7f2498288cc8085ec4d35b` |
| 29-oxo | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `0f55ff1de6f1a3ebcf644f24d1b6b49d60a07d7084ea811d188ac5643938af9d` |
| 30-space-traffic | BEHAVIOR UNVERIFIED — no input screen change | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `78422f8546a9aef83c2a507c1eff73151ce3c4c9ae24920f2197bcb744dd6009` |
| 31-dam-eaters | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `174216fa5338ee8e3694b8e3cd2224f12cd42c39b7b921bf8948f9efd7473a0f` |
| 32-buzzy-bee | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `bf61bb3550aeee0bb6758518dfcaa03aec5865486ff5922ec1a97b545d86f014` |
| 33-heli-bomber | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `713bcbb2c2e3dc015ee7365f130cb567226ddb26d459f5c30c9d248beb9302d9` |
| 35-giant-rats | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `b03aea10367e0e4110ec8dc7ef973c2a8b195746283caf090dff06428ba4e3da` |
| 37-xmas-eve | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `352bd368c2fa63ad9745871c0b83c644c954060456f71a8e332f838dd1733341` |
| 39-flying-geese | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `b7b498b4abc20b9aecb5223fc6459cd49708daf3cf3a15fd0dec8d580212fa36` |
| 40-wordsum | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `73a7247247ae378856ef2871312af3eb4338bf1290b087ab808a2e175ca851bf` |
| 42-bricklayer | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `a5889d9f1c4775f73921df06a81088c1aaf45c258d6d3a4cc3e2129f92ced84e` |
| 43-dogfight | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `b4e77fb7120207a42e919fa3e8501b890238036aa9ab35ce25b6807dde26d588` |
| 47-exocet | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `007da768b3901a4de7adebcad0c4ba6f92604cc6f49b931428476a46cdc34ffa` |
| 49-drag-racer | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `1fd66b05726a92c80c775919f1e45e097056769da2f84a68aeadd3a83878932d` |
| 50-moonlander | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `7b0dca0638a562b993fe16327fc801120e5d9846626b11d8478bac1f7c8e6ab4` |
| 54-swordsman | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `82f3eb32e096bb7c826af55c0d53b58942ba24193b98d140a89d2c30750c6906` |
| 56-roots | BEHAVIOR UNVERIFIED — no input screen change | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `36f63706334bf028f444468c4d9d94572f0e8df6f4e02abc303b9b2d98359846` |
| 57-bulls-and-cows | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `6d45826639c4eadb950df94e4a3442dfa4a86b8d3af0a127ec4b2b7f2734c254` |
| 59-mushroom-invasion | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `360793a9ea2169b49691b1ad3ae6a21fb05d633e54494ccbb19cfefe47a9ad1b` |
| 60-countabout | SCREEN RESPONSE VERIFIED | SCREEN RESPONSE VERIFIED; GAMEPLAY UNVERIFIED | `f88fdeff15387c8f58f73e40b854efc7a00dcad0768667bce024e89b6b00b8d3` |

Prior unresolved cases: **01-minelay, 07-critical-path-analysis,
23-biorhythms, 30-space-traffic, 56-roots**. Those five passed a
screen-response check with the default compiled ZX-UX INPUT source.

## Six production rebuilt native pairs

Each row gives SHA-256 of *both* independently built SSX images and of the
actual published game-bin file. Whole SSX-file bytes and image+BSS+stack
must independently fit the unchanged 14,000-byte loader.

| Game | BAS=TZX=published SHA-256 | File | Image | BSS | Stack | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 01-minelay | `4f574b5eaa66e1c3fb10f7418f1c05b97428043fff2971782137ab4b7413844f` | 11205 | 9904 | 381 | 384 | 10669 |
| 07-critical-path-analysis | `0500c51018841cdd705cb2fcaac8369be3508441d076948327af3dd2ffed5e4b` | 12031 | 10580 | 2885 | 384 | 13849 |
| 23-biorhythms | `e4b7ce25fa1e4e6dabf708e266d63f99fa60f12fee3a1c25fcf7c24ef89f48a9` | 8686 | 7749 | 160 | 384 | 8293 |
| 30-space-traffic | `5c7153706186ca60a5d12f47f1259ece8e19d9c32e3bb90a1e12e87a038f77e7` | 10941 | 9716 | 900 | 384 | 11000 |
| 39-flying-geese | `2c1608d17adfa584a1df4e8c4e6487e9853b3ef55437a724f2e4bcd8b867e542` | 8907 | 7889 | 501 | 384 | 8774 |
| 56-roots | `14034761751e4b2ca8a19ceffd10423e4459aeb16131304072f88c267e2099d2` | 11430 | 10365 | 835 | 384 | 11584 |

## Targeted behavior and limitations

- Default CLI now selects `--input-backend zxux` for true INPUT tokens;
  `--input-backend rom` retains the exact original HiSoft reference.
- INPUT line handling has bounded workspace, guards protected memory,
  supports echoed keys, numeric invalid-entry re-prompt, DELETE, EDIT-clear,
  LEFT/RIGHT cursor editing and insertion. UP is inert in INPUT; DOWN is
  a guarded STOP with clean shell return. Unsupported control keys fail
  closed instead of corrupting text. No full non-INPUT ROM editor parity claimed.
- Production Flying Geese: real 100-shot GAME OVER, ENTER launches a new
  round in the unchanged ZX-UX kernel, separately tested with native SSX.
- Other gameplay-specific tests separately verify available complete rounds,
  scoring, replay, STOP/shell restoration, and isolation; individual game
  playthrough coverage beyond those tests remains incomplete.

## Test result record

All per-game raw stdout, stderr, exit and elapsed logs stay untracked under
`build/tmp/`; this report retains SHA-256 digests of their exact bytes.
Genuine screenshots from published Flying Geese were captured via the real
ZX-UX loader and `rvm.write_png`; original game source and frozen tape used:

- `39-flying-geese-production-gameover.png`: SHA-256 `1bdab0f5b031d2266b43f4f86d964950c2baef4cd020bb4ba55e2cb75ef8dd09`.
- `39-flying-geese-production-replay.png`: SHA-256 `b92831349049d58c59f7c1e5fcd6bad404e50ea2e3dbcee60c68278db3abbd85`.

The program displays `GAME OVER`, `SCORE:5 IN 100 SHOTS` at the first capture;
after ENTER the screen displays a new `SHOTS:` round without `GAME OVER`.
The production SSX SHA-256 is `2c1608d17adfa584a1df4e8c4e6487e9853b3ef55437a724f2e4bcd8b867e542`.
This verifies game-over and replay, **not** completion of the new round.
Unsupported ROM behavior and all-game victory are not asserted. No optimizer,
post-link binary patch or external binary editor was invoked.
