# RBC original BASIC: first safety-policy token survey (2026-10-23)

This is a **read-only token survey**, not a new compiler PASS result, control-flow
proof, executable packaging test, or gameplay acceptance.

Source: `main` commit `f459e2a43e97cb164370f69bdaa983fb5746c141`,
tree `fc67d86b0205591001b7456c110e46ec39d51151`.
The source archive's 60 TZX inputs matched all 60 Git blob identities from that
tree. Its 60 BAS inputs matched the Git blobs after CRLF-to-LF line ending
conversion; this was for read-only analysis and did not change the originals.

All 120 original inputs parsed, with equal source-line totals and identical
USR, POKE and VAL operation line/status sequences for each text/tape pair.
This confirms the surveyed operations across both original input formats,
not every byte of runtime interpretation.

Per original input form (the other form has the same counts):

- 161 USR expressions: 151 literal graphics-character arguments, 8 CHR$
  expressions needing type/range proof, one string variable needing a length
  proof, and **one numeric machine-code call**.
- 178 POKE destinations: 44 constant arithmetic addresses ready for the
  independent memory-policy check; 134 variable-dependent destinations
  **still needing exact possible-address proofs**. No dynamic entry is marked
  approved merely because it appears in a bounded loop.
- 40 VAL expressions require confirmation that dynamic string evaluation
  cannot invoke a machine-code USR or evade the address checks.

**Confirmed incompatibility:** `55-hangman`, BASIC line 7080,
`LET I=USR 3280` occurs in both original forms. Under the new policy this
must fail at compilation with the actual BASIC line and an explicit reason.
Existing pre-policy native-start results for Hangman are not policy passes.

POKE line inventory below. Repeated line numbers mean separate POKE statements
on that same BASIC line. Constant means the destination expression evaluates
without program state; all other addresses remain unproved here. The latter
include regular UDG setup loops. Blank means no such occurrence. This is a
triage list, not a safety approval or a control-flow proof.

| Program | Constant POKE lines | POKE lines needing proof |
|---|---|---|
|01-minelay||9000|
|02-fall-guy|9570,9640|9000|
|03-tug-of-war||8000|
|04-horse-race||9000|
|05-championship-boxing||9000|
|06-motocross|25,25,25|9000|
|07-critical-path-analysis|||
|08-chomper||9000|
|09-battleships|5|9000|
|10-tanx||9000|
|11-defend||2000|
|12-flying-bomb||610,610,610,620,630,640,9010|
|13-radio-power|20,5120,5151,5800||
|14-scuba|5,632,632,3000,3000,3270,3270|5008,9020|
|15-endings|1||
|16-snap|15|70,240|
|17-paypackets|535||
|18-newmarket||3010,3110,3210,3310,3410,3510|
|19-hobday-expenses|15||
|20-ambush||615,620,620,630,650,655,655,660,660|
|21-numbers|15,15|555,560|
|22-top-trainer|672,675||
|23-biorhythms|||
|24-aben||1000|
|25-galaxians||9000|
|26-sheep-dog-trials||6010|
|27-picture-pairs|15|70,210,260,307,335,520,520,530|
|28-dam-busters||1000|
|29-oxo||25,25|
|30-space-traffic|110|9000|
|31-dam-eaters||9000|
|32-buzzy-bee|50,50,50|9710|
|33-heli-bomber||2510|
|34-grand-prix||9000|
|35-giant-rats||9000|
|36-postman||9000|
|37-xmas-eve||9000|
|38-morse-tutor|10||
|39-flying-geese||610,610,610,630,630,640,650,660,660|
|40-wordsum|||
|41-asset-stripper|||
|42-bricklayer||190|
|43-dogfight||9170|
|44-evolution-1||1000,2030,3030|
|45-evolution-2||100,1040|
|46-evolution-3|3|20|
|47-exocet||9020|
|48-energy-field||8010|
|49-drag-racer||9330|
|50-moonlander||9300|
|51-anagrammatic|20,305||
|52-stellar-run|120,120,140,140,1010|8100|
|53-russian-roulette|||
|54-swordsman|2,4106||
|55-hangman|5||
|56-roots|20|50,60|
|57-bulls-and-cows||9020|
|58-invaders||465,465,470,470,480,480,480,480,480,490,490,490,497|
|59-mushroom-invasion|3015|750,760,770,780,995,996|
|60-countabout||9050,9060,9070,9090,9100,9100,9110,9120,9150,9160,9170,9180,9190,9200,9210,9220,9230,9240,9250,9260,9270,9290,9490,9500,9510,9520,9530,9540,9550,9550|

Scanner development checks: five focused unit tests passed, including string,
REM, DATA, numeric USR context, constant POKE and tokenized input cases.
The local private checker accepted this report and the scanner. No native RBC
FAST/BATCH/FULL rerun was performed under the newly approved policy.

Prior last validated FULL: 111/121 combined linked/size-approved inputs at
source revision `1c96559ba5ff3ba423374f68e15e914d9d30838c`, action
`40031609347`; ten size failures across five titles. This is **pre-policy**.
Track B remains **3/60** accepted; the next port is `02-fall-guy`.

Next: enforce numeric-USR rejection in RBC; prove exact POKE target sets and
then apply unchanged memory rules; run FAST, BATCH and FULL with real native
outcomes. Do not turn the old 111/121 into an untested new policy score.