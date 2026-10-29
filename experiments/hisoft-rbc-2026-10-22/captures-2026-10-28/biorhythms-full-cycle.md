# Biorhythms: native six-date chart and new entry cycle (2026-10-29 UTC)

The original published `23-biorhythms.ssx` ran unchanged inside the genuine
ZX-UX 48K kernel and Z80 emulator. Its real keyboard accepted six numeric
inputs: birth date **28/10/1980** and requested date **28/10/2026**. The
program advanced through its physical, emotional and intellectual cycle
branches and rendered its chart. The framebuffer showed
`Biorhythm for     28/10/2026+` and `Press a key to restart`.

A real `a` key then returned the same live native process to the fresh
`BIORHYTHMS` input form: birth year/month/day, requested year/month/day,
and `Enter details now (numeric)`. This proves the functional input-to-chart
cycle and restart. It does not establish independent mathematical accuracy
of the plotted curves, all date ranges, STOP, or shell return.

No original BAS/TZX, linked SSX, ROM, kernel, machine state, random values,
or framebuffer pixels were changed. The test checks the original input
bytes again after the live kernel run.

From repository root, with the frozen tape in `build/out/ZX-UX.tzx`, its
matching `kernel.json`, and the checked original `font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_BIORHYTHMS_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover \
  -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_biorhythms_full_cycle.py -v
```

The native test and six separate ROM syntax tests passed. One additional
INPUT isolation test skipped because its external compiler inputs were
unavailable, so its result is not included in the pass count.

| Checked input or capture | Bytes | SHA-256 |
| --- | ---: | --- |
| Original BAS | 3112 | `6ffd91bef183295ea4592b54c33d6c665438a4e80528ef130bf3ea210fad12ab` |
| Original TZX | 3297 | `b6741e563f8ca74529334c5e6b445557e029420efb87ba5e7a7c261e4e7e5a7d` |
| Published native SSX | 8686 | `e4b7ce25fa1e4e6dabf708e266d63f99fa60f12fee3a1c25fcf7c24ef89f48a9` |
| Original ROM | 16384 | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| Frozen ZX-UX tape | 29742 | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| `biorhythms-chart.png` | 5857 | `5cd8493502e322b8bb96dabfcbd0ad9c4c83d4904915869222d7cb78ef776261` |
| `biorhythms-restarted.png` | 3147 | `5ecbd090f5eff9e36e9af5fd9ba2c17e4f366f27eaaae8cfdc0ab129a19a2489` |

The native SSX file is **8,686** bytes. Image **7,749**, BSS **160**, stack
**384**, image+BSS+stack **8,293**, both below the unchanged **14,000** limit.
The two PNGs were captured directly from genuine 6,912-byte Spectrum
framebuffers using `rvm.write_png`; no screenshot pixels were constructed.
