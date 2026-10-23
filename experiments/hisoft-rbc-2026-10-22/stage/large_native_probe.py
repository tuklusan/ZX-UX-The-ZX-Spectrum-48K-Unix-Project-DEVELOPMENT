"""Record actual ZX-UX loader failures for compiled large BASIC programs."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def inspect(root: Path, out: Path):
    sys.path.insert(0, str(root / "dist/sdk/bin/py"))
    import rvm

    system = root / "dist/zx-ux/tzx/ZX-UX.tzx"
    result_path = out / "rbc-60-results-shard-1.json"
    rows = json.loads(result_path.read_text())
    by_name = {x["program"]: x for x in rows}
    failures = []
    for name in ("19-hobday-expenses-tape", "22-top-trainer-tape"):
        binary = out / (name + ".ssx")
        if name not in by_name or not binary.exists():
            print("LOADDIAG", name, "unavailable or not compiled", flush=True)
            continue
        options = rvm.Options()
        options.prog = str(binary)
        options.args = []
        options.keys = ""
        options.frames = 120
        options.system = str(system)
        options.cache = True
        options.headless = True
        run = rvm.Runner(options)
        diagnostic = {"frames": 0, "started": False, "reason": None, "screen": ""}
        try:
            run.start()
            for frame in range(3120):
                run.frame()
                diagnostic["frames"] = frame + 1
                fg = run.fg
                if fg is not None and fg.started is not None:
                    diagnostic["started"] = True
                    break
                stop = run.check(120)
                if stop:
                    diagnostic["reason"] = stop
                    break
            bitmap, _ = run.picture()
            diagnostic["screen"] = rvm.screen_text(bitmap)
            diagnostic["job"] = run.fg.describe() if run.fg else None
        except Exception as exc:
            diagnostic["exception"] = repr(exc)
        by_name[name]["native_diagnostic"] = diagnostic
        print("LOADDIAG", name, json.dumps(diagnostic), flush=True)
        if not diagnostic["started"]:
            failures.append(name)
    result_path.write_text(json.dumps(rows, indent=2) + "\n")
    if failures:
        raise RuntimeError("Large native programs did not start: " + ", ".join(failures))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: large_native_probe.py PROJECT_ROOT TRIAL_DIR")
    inspect(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
