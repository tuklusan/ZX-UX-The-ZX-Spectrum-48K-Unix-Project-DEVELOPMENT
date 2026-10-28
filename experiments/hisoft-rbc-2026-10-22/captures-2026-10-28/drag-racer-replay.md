# Original Drag Racer: engine failure and restart

Two separate real ZX-UX emulator boots used the **published, unchanged**
`49-drag-racer.ssx`. Both started the original native game. The first
reached the `Engine blown` and `Press any key to restart` screen. On the
second run, a further physical `x` key cleared both messages, returned
to the speedometer screen and continued the original game loop.

The test checks the original BAS, TZX and SSX bytes before and after each
run, the native loader limit, process screen ownership, and actual 48K
framebuffers. It proves one engine-failure/restart cycle, not completion of
every racing strategy or every one of the 34 native games.

Reproduce from the repository root with the original rebuilt ZX-UX tape:

```sh
python3 -m unittest discover -s experiments/hisoft-rbc-2026-10-22/tests \
  -p test_native_drag_racer_replay.py -v
```

| Input or captured screen | Bytes | SHA-256 |
| --- | ---: | --- |
| BAS | 3,586 | `cddd2cfc4c841e0320dd9ab126be47410e39a787dfddbbaff03bb880ffd3fb5e` |
| TZX | 3,678 | `3945359b9920b9b3d53c1c9b81e7d6d5057b4ce0f96e56ad8cbe070e2a8ebdd5` |
| Published SSX | 8,124 | `42b8262399e40c22e90c96871da7575bb319ca206a81eb996bf951824943a447` |
| Engine blown PNG | 4,026 | `6fae7f6cb0627f9d3d7d75116107d721ec13e20a3b82f2947be81041a4abde41` |
| After restart key PNG | 3,686 | `d4d98649e9ef39614d079447ee2a05d79cf3e534434c0cbf9fa4fc327b01ed42` |

Both captures are direct ZX-UX/Z80 emulator framebuffers. No image editing,
BASIC source changes or binary fixes were used.
