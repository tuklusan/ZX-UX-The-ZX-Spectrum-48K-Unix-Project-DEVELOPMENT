# Roots: original native custom calculation (2026-10-29 UTC)

The unchanged published `56-roots.ssx` ran in the actual ZX-UX 48K loader and Z80 emulator. Actual keyboard ENTER keys advanced the source's Newton/Raphson introduction and demonstration. The real keyboard then supplied original source inputs `N=25` and `R=2`; the native program rendered `THE 2 ROOT OF 25 IS`, `5`, and `5 ^ 2 = 25`, followed by `ENTER 'Q' TO QUIT`. This is one completed custom numerical calculation, **not** proof of every root, numerical precision, successful `Q`/STOP, or shell return. A separate `q`/ENTER attempt did not establish STOP and is **not** counted as an exit pass.

Repeat with the original system tape at `build/out/ZX-UX.tzx`, checked 48K ROM, and source-verified `font32.bin` at `build/tmp/rbc-recovered/rbc/font32.bin`:

```sh
PYTHONDONTWRITEBYTECODE=1 \
RBC_ROOTS_CAPTURE_DIR=experiments/hisoft-rbc-2026-10-22/captures-2026-10-28 \
python3 -B -m unittest discover -s \
  experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_roots_custom_calculation.py -v
```

One native emulator test passed; six independent ROM syntax tests passed. The test checks original game/ROM bytes before and after, native 48K loader admission, active process screen ownership, genuine framebuffers, and the distinct numerical output. No original BASIC/TZX/SSX, emulator, ROM, kernel, process state, random values, or framebuffer pixels were patched.

| Source file or capture | Bytes | SHA-256 |
| --- | ---: | --- |
| `56-roots.bas` | 5,282 | `f215e95bda4a945f105d008e2986cfde2d69334a23bb87511de1f3a594ae392a` |
| `56-roots.tzx` | 5,408 | `cfe88b43867e8de3d69d8f2d0b47c86e8809c2317d8bb710e2445dd12843c5b3` |
| `56-roots.ssx` | 11,430 | `14034761751e4b2ca8a19ceffd10423e4459aeb16131304072f88c267e2099d2` |
| Original `48.rom` | 16,384 | `d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42` |
| Frozen ZX-UX tape | 29,742 | `676d52db288ee383e2bbe449be9c01e10ba5b61a8c6d1efd218cef627fdef597` |
| `roots-25-square-calculated.png` | 4,385 | `4e074696aa3c7ed61581ea0ca1a4d2b0990a8ce2e71252e249bf07339496617c` |

SSX admission: file 11,430 bytes; native image 10,365; BSS 835; stack 384; image+BSS+stack 11,584; both under unchanged default 14,000. PNG is from an authentic 6,912-byte Spectrum framebuffer using `rvm.write_png`, without alteration.
