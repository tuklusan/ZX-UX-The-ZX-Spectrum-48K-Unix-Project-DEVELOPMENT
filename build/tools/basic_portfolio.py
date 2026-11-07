#!/usr/bin/env python3
"""Capture actual ZX-UX RBC SSX screens in RVM, never archival tape pictures."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from html import escape
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
sys.path[:0] = [str(DIST / 'sdk/bin/py'), str(ROOT / 'src/zx-ux-sdk/tools')]
from basicpack import tape_name
sys.path.insert(0, str(DIST / 'sdk/bin/py'))  # basicpack imports the source SDK
import rvm
import zxscreen
from capture_quality import bitmap_ink, program_output_lines
from capture_replay import steps, rvm_actions, recorded_first_input_wait


def cases():
    root = DIST / 'assets/rbc-bin'
    for collection in sorted(root.iterdir()) if root.is_dir() else ():
        if not collection.is_dir():
            continue
        for ssx in sorted((collection / 'ssx').glob('*.ssx')):
            original = DIST / 'assets/basic-src' / collection.name / ssx.stem
            if not any(original.glob('*.bas')):
                raise RuntimeError('missing original BASIC source: ' + ssx.stem)
            yield collection.name, ssx, tape_name(ssx.stem)


def write_gallery(out: Path, engine: str):
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<title>ZX-UX RBC — %s</title>' % escape(engine),
             '<h1>ZX-UX RBC — %s</h1>' % escape(engine),
             '<p>Native ZX-UX program screens; a screen alone is not gameplay verification.</p>']
    count = 0
    for collection in sorted(p for p in out.iterdir() if p.is_dir()) if out.is_dir() else ():
        parts.append('<h2>%s</h2>' % escape(collection.name))
        for png in sorted(collection.glob('*.png')):
            rel = collection.name + '/' + png.name
            original = DIST / 'assets/basic-src' / collection.name / png.stem
            links = []
            for suffix in ('.bas', '.tzx'):
                for source in sorted(original.glob('*' + suffix)):
                    href = quote(__import__('os').path.relpath(source, out).replace('\\', '/'), safe='/')
                    links.append('<a href="%s">%s</a>' %
                                 (escape(href, quote=True), escape(source.name)))
            parts.append('<figure><a href="%s"><img src="%s" alt="%s" width="320"></a>'
                         '<figcaption>%s — %s</figcaption></figure>' %
                         (escape(rel, quote=True), escape(rel, quote=True), escape(png.stem),
                          escape(png.stem), ' · '.join(links)))
            count += 1
    parts.append('<footer>%d native captures</footer></html>' % count)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    return count


def run_one(collection: str, ssx: Path, label: str, frames: int):
    # The short cassette alias is required by the unmodified ZX-UX loader.
    recorded = steps(collection, ssx.stem)
    start_delay = recorded_first_input_wait(collection, ssx.stem, recorded)
    wait_for_ready = start_delay is not None
    checkpoints = ()
    if wait_for_ready:
        actions = rvm_actions(recorded)
        checkpoints = tuple(len(actions) - len(rvm_actions(recorded[:index + 1]))
                            for index, item in enumerate(recorded) if item[0] == 'C')
    with tempfile.TemporaryDirectory(prefix='zxux-basic-rvm-') as temporary:
        alias = Path(temporary) / (label + '.ssx')
        shutil.copyfile(ssx, alias)
        if alias.read_bytes() != ssx.read_bytes():
            raise RuntimeError('RVM input changed')
        opt = rvm.Options()
        opt.prog = str(alias)
        opt.system = str(DIST / 'zx-ux/tzx/ZX-UX.tzx')
        opt.headless = True
        runner = rvm.Runner(opt)
        runner.start()
        shell_screen = bytes(runner.session.m.screen())
        shell_text = zxscreen.screen_text(shell_screen)
        scripted = False
        first_key_remaining = None
        first_output = None
        post_key = None
        post_samples = 0
        selected = None
        best = -1
        previous_display = None
        unchanged = 0
        candidates = []
        pending_checkpoints = list(checkpoints)
        for frame in range(frames + 3000):
            runner.frame()
            job = runner.fg
            if job.started is not None and not scripted:
                ready = True
                if wait_for_ready:
                    owned = runner.session.program_screen(job)
                    if owned is None:
                        ready = False
                    else:
                        display = bytes(owned[0])
                        unchanged = unchanged + 1 if display == previous_display else 0
                        previous_display = display
                        ready = (frame - job.started >= start_delay
                                 and unchanged >= 24 and bitmap_ink(display) >= 500)
                if ready:
                    if recorded:
                        actions = rvm_actions(recorded)
                        first_key = next((i for i, action in enumerate(actions)
                                          if action[0] in ('keys', 'press')), None)
                        runner.session.kb.add(actions)
                        if first_key is not None:
                            first_key_remaining = (len(runner.session.kb.queue)
                                                   - first_key - 1)
                    scripted = True
            if job.started is not None and (selected is None or frame % 10 == 0):
                # Console programs print to the shared tty. They need not
                # own a private screen; the old code captured None for them.
                owned = runner.session.program_screen(job)
                pixels, border = (owned if owned is not None else
                                  (runner.session.m.screen(), runner.session.m.border))
                if len(pixels) == 6912:
                    current = bytes(pixels)
                    output = program_output_lines(zxscreen.screen_text(current),
                                                  shell_text)
                    if output or (owned is not None and current != shell_screen):
                        score = bitmap_ink(current)
                        if score >= 64:
                            if first_output is None:
                                first_output = current
                            if (first_key_remaining is not None
                                    and len(runner.session.kb.queue) <= first_key_remaining
                                    and current != first_output):
                                post_samples += 1
                                if post_samples >= 2 and post_key is None:
                                    post_key = (current, border)
                            if score > best:
                                selected, best = (current, border), score
                            if wait_for_ready and scripted:
                                while (pending_checkpoints and len(runner.session.kb.queue)
                                       <= pending_checkpoints[0]):
                                    pending_checkpoints.pop(0)
                                    candidates.append([current, border, frame + 25, 0])
                                for candidate in candidates:
                                    if frame <= candidate[2]:
                                        motion = sum((a ^ b).bit_count() for a, b in
                                                     zip(candidate[0][:6144], current[:6144]))
                                        candidate[3] = max(candidate[3], motion)
            reason = runner.check(limit=frames, interactive=wait_for_ready and not scripted)
            if reason:
                runner.why = reason
                break
        job = runner.fg
        if job.started is None or selected is None:
            raise RuntimeError(
                'no independently observed native program output: ' + ssx.name
                + f' started={job.started} loading={job.loading}'
                + f' ended={job.ended} status={job.status} why={runner.why}')
        if recorded:
            if post_key is None:
                raise RuntimeError('no changed native screen after recorded input: '
                                   + ssx.stem
                                   + f' started={job.started} ended={job.ended}'
                                   + f' status={job.status} why={runner.why}'
                                   + f' queued={len(runner.session.kb.queue)}'
                                   + f' first_key_remaining={first_key_remaining}'
                                   + f' post_samples={post_samples}'
                                   + ' screen=' + repr(zxscreen.screen_text(
                                       runner.session.m.screen())))
            selected = post_key
            if wait_for_ready and candidates:
                # Prefer changing native displays to settled title, crash or
                # end-of-game screens.
                active = max(candidates, key=lambda candidate: candidate[3])
                if active[3] > 0:
                    selected = (active[0], active[1])
        image, border = selected
        if len(image) != 6912:
            raise RuntimeError('invalid Spectrum screen')
        out = DIST / 'screenshots/rbc/rvm' / collection / (ssx.stem + '.png')
        out.parent.mkdir(parents=True, exist_ok=True)
        rvm.write_png(image, str(out), border)
        if recorded and runner.session.kb.queue:
            print('RBC RVM WARNING:', ssx.stem, 'recorded keys unfinished',
                  file=sys.stderr, flush=True)
        print('RBC RVM', ssx.stem, runner.why, 'ink', best, flush=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--only', default='')
    p.add_argument('--frames', type=int, default=1500)
    p.add_argument('--jobs', type=int, default=12)
    args = p.parse_args(argv)
    if not 1 <= args.jobs <= 16:
        p.error('--jobs must be 1..16')
    wanted = set(args.only.split(',')) if args.only else None
    found, failures = set(), []
    tasks = []
    for collection, ssx, label in cases():
        if wanted is not None and ssx.stem not in wanted:
            continue
        found.add(ssx.stem)
        tasks.append((collection, ssx, label))
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        pending = {pool.submit(run_one, *case, args.frames): case[1].stem
                   for case in tasks}
        for future in as_completed(pending):
            name = pending[future]
            try:
                future.result()
            except Exception as e:
                print('RBC RVM FAIL:', name, str(e), file=sys.stderr, flush=True)
                failures.append(name)
    if wanted is not None:
        failures.extend(sorted(wanted - found))
    out = DIST / 'screenshots/rbc/rvm'
    count = write_gallery(out, 'RVM')
    if wanted is None and count != len(found):
        failures.append('incomplete RBC RVM gallery')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
