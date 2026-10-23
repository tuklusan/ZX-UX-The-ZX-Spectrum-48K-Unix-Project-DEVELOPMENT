#!/usr/bin/env python3
"""Review prior runs and keep test results before cleanup."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

REPO = 'tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT'
ROOT = Path('experiments/hisoft-rbc-2026-10-22')
BASELINE = ROOT / 'rbc-run-39878801410-results.zip'
BASELINE_DIGEST = '3d5b45ae2c09f3346bb19792b76ea74353a2d799ce50db38463d01c587b5445c'
OUT = ROOT / 'results'
SUMMARY = OUT / 'ACTIONS-CLEANUP-SUMMARY.json'
FAST_RECORD = OUT / 'LATEST-RBC-RESULTS.json'
FULL_RECORD = OUT / 'LATEST-RBC-FULL.json'


def command(*args, check=True, timeout=60):
    return subprocess.run(args, capture_output=True, text=True,
                          check=check, timeout=timeout)


def api(path, method='GET'):
    arguments = ['gh', 'api']
    if method != 'GET':
        arguments += ['--method', method]
    response = command(*arguments, f'repos/{REPO}/{path}')
    return json.loads(response.stdout) if method == 'GET' else None


def verify_baseline(root):
    path = root / BASELINE
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != BASELINE_DIGEST:
        raise RuntimeError('Permanent 121-input result bundle is missing or changed')
    with zipfile.ZipFile(path) as zf:
        files = [x for x in zf.namelist()
                 if Path(x).name.startswith('rbc-60-results-shard-') and x.endswith('.json')]
        rows = [row for name in files for row in json.loads(zf.read(name))]
    if len(rows) != 121 or len({x['program'] for x in rows}) != 121:
        raise RuntimeError('Permanent compiler result set is incomplete')
    return sum(x['ok'] for x in rows)


def list_runs():
    result = []
    page = 1
    while True:
        data = api(f'actions/runs?per_page=100&page={page}')
        chunk = data['workflow_runs']
        result.extend(chunk)
        if len(chunk) < 100:
            return result
        page += 1
        if page > 100:
            raise RuntimeError('Unexpectedly large Actions run collection')


def result_candidates(runs):
    return [run for run in sorted(runs, key=lambda x: x['id'], reverse=True)
            if run['name'] == 'RBC Python compiler trial'
            and run['status'] == 'completed'
            and run['head_branch'] == 'main']


def verify_result(data, sha):
    if data.get('mode') not in ('fast', 'batch', 'full') or data.get('revision') != sha:
        raise RuntimeError('Input report does not match source revision')
    rows = data.get('inputs')
    expected = data.get('expected_inputs')
    if (type(expected) is not int or not 1 <= expected <= 121
            or not isinstance(rows, list) or len(rows) != expected
            or len({x['program'] for x in rows}) != expected):
        raise RuntimeError('Input record count is incomplete')
    if data.get('mode') == 'fast' and (expected < 11 or expected % 2 != 1):
        raise RuntimeError('Incorrect FAST input count')
    if data.get('mode') == 'full' and expected != 121:
        raise RuntimeError('Incorrect FULL input count')
    if data.get('invalid'):
        raise RuntimeError('Input result collection has errors')
    return data


def download_result(run, root):
    with tempfile.TemporaryDirectory() as td:
        command('gh', 'run', 'download', str(run['id']), '--repo', REPO,
                '--name', 'rbc-input-summary', '--dir', td, timeout=120)
        paths = list(Path(td).rglob('inputs.json'))
        if len(paths) != 1:
            raise RuntimeError('Expected exactly one input summary')
        result = verify_result(json.loads(paths[0].read_text()), run['head_sha'])
    return {'source_run': run['id'], 'source_sha': run['head_sha'],
            'mode': result['mode'], 'expected_inputs': result['expected_inputs'],
            'passed_inputs': sum(x.get('ok') is True for x in result['inputs']),
            'result': result}


def read_saved_result(root):
    try:
        data = json.loads((root / FAST_RECORD).read_text())
        result = verify_result(data['result'], data['source_sha'])
        if (type(data['source_run']) is not int or data['source_run'] <= 0
                or data['mode'] != result['mode']
                or data['expected_inputs'] != result['expected_inputs']
                or data['passed_inputs'] != sum(x.get('ok') is True
                                                for x in result['inputs'])):
            raise RuntimeError('Stored compiler results disagree with their summary')
        return data
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('No verified permanent compiler result to reuse') from exc


def rollup(runs, current_id, fast, baseline_pass):
    eligible = [r for r in runs if r['status'] == 'completed' and r['id'] != current_id]
    counts = collections.Counter((r['name'], r.get('conclusion')) for r in eligible)
    return {'schema': 1, 'source': 'GitHub Actions API',
            'baseline_file': str(BASELINE), 'baseline_sha256': BASELINE_DIGEST,
            'baseline_inputs': 121, 'baseline_compiled': baseline_pass,
            'latest_source_run': fast['source_run'],
            'latest_source_sha': fast['source_sha'],
            'latest_compiled': fast['passed_inputs'],
            'eligible_completed_runs': len(eligible),
            'workflow_outcomes': [{'workflow': k[0], 'conclusion': k[1], 'count': v}
                                  for k, v in sorted(counts.items())],
            'cleanup_current_run_excluded': current_id,
            'cleared_run_ids': [], 'delete_errors': [],
            'note': 'Old run logs are not proof of completed 60-program compatibility.'}


def stage_and_publish(root, files):
    names = [str(path) for path in files]
    command('git', 'add', '--', *names)
    diff = command('git', 'diff', '--cached', '--name-only').stdout.splitlines()
    if not set(diff).issubset(set(names)):
        raise RuntimeError('Unexpected staged changes, publication refused: ' + repr(diff))
    if not diff:
        for path in files:
            stored = command('git', 'show', 'HEAD:' + str(path)).stdout
            if stored.encode() != (root / path).read_bytes():
                raise RuntimeError('Unchanged result file differs from current commit')
        return
    base = command('git', 'rev-parse', 'HEAD').stdout.strip()
    upstream = command('git', 'ls-remote', 'origin', 'refs/heads/main').stdout.split()[0]
    if upstream != base:
        raise RuntimeError('main moved before reporting results')
    command('git', 'config', 'user.name', 'ZX-UX Actions')
    command('git', 'config', 'user.email', 'actions@users.noreply.github.com')
    command('git', 'commit', '-m', 'Save completed Actions test results')
    command('git', 'push', 'origin', 'HEAD:main', timeout=120)
    # Verify exact bytes came back from the permanent remote branch.
    command('git', 'fetch', '-q', 'origin', 'main', timeout=120)
    for path in files:
        remote = command('git', 'show', 'origin/main:' + str(path)).stdout
        if remote.encode() != (root / path).read_bytes():
            raise RuntimeError('Remote result bundle mismatch: ' + str(path))


def execute(root, current_id):
    # Keep only useful current compiler results; no history rollup or audit log.
    verify_baseline(root)
    runs = list_runs()
    record = None
    protected_ids = set()
    for candidate in result_candidates(runs):
        try:
            record = download_result(candidate, root)
            break
        except (subprocess.CalledProcessError, RuntimeError, OSError, ValueError):
            protected_ids.add(candidate['id'])
    if record is None:
        record = read_saved_result(root)
    (root / OUT).mkdir(parents=True, exist_ok=True)
    files = [FAST_RECORD]
    if record['mode'] == 'full':
        files.append(FULL_RECORD)
    for path in files:
        (root / path).write_text(json.dumps(record, indent=2) + '\n')
    stage_and_publish(root, tuple(files))
    # Only remove runs whose required reports are safely stored (or the
    # already-finished non-RBC runs). An unverified RBC run is protected.
    targets = [x for x in runs if x['status'] == 'completed'
               and x['id'] != current_id and x['id'] not in protected_ids]
    errors = []
    deleted = 0
    for run in targets:
        try:
            api(f"actions/runs/{run['id']}", method='DELETE')
            deleted += 1
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            errors.append((run['id'], str(exc)))
    print(f'Consumed Actions runs removed: {deleted}/{len(targets)}')
    if errors:
        raise RuntimeError(f'Actions cleanup had {len(errors)} failures: {errors[:3]}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if os.environ.get('GITHUB_REPOSITORY') != REPO or os.environ.get('GITHUB_REF') != 'refs/heads/main':
        raise SystemExit('Cleanup is restricted to development main')
    if not os.environ.get('GH_TOKEN'):
        raise SystemExit('GitHub Actions token is unavailable')
    current_id = int(os.environ['GITHUB_RUN_ID'])
    root = Path.cwd().resolve()
    if not args.execute:
        verify_baseline(root)
        runs = list_runs()
        print('Dry run: completed eligible runs:', sum(r['status'] == 'completed' and r['id'] != current_id for r in runs))
        return
    execute(root, current_id)


if __name__ == '__main__':
    main()