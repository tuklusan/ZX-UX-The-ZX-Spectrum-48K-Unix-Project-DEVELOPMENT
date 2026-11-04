#!/usr/bin/env python3
"""Check and optionally publish an already verified clean-room build."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
REPO = 'tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT'
SOURCE = 'src/assets/basic-src/original-sinclair-basic-collections'
RELEASE_HEAD = '4094901e5132f69e7c6539076431fb9ad2f9d831'
RUN_ID = '41813999141'
MESSAGE = 'Rebuild verified RBC collections and both screenshot portfolios'
# Text checked with the unchanged private checker, along with MESSAGE and push command.
CHECKED_TEXT_SHA256 = '2f4942182be2119d77b07b9d5b10b56b251541d5137adadc6235a2ca1e4cf638'
COLLECTIONS = ('Granada-Publishing', 'www.thespectrumshow.net')
COMPILERS = {'c48-bin': 61, 'rbc-bin': 96, 'forth-bin': 38,
             'pascal-bin': 25, 'fortran-bin': 42}
CAPTURES = {'c48-bin': 63, 'rbc-bin': 96, 'forth-bin': 38,
            'pascal-bin': 25, 'fortran-bin': 42}
STAGES = ('build', 'c48-rvm', 'rbc-rvm', 'compilers-rvm',
          'c48-fuse', 'rbc-fuse', 'compilers-fuse', 'gallery', 'tests')


def fail(reason):
    raise RuntimeError(reason)


def command(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd or ROOT, stderr=subprocess.PIPE)


def git(*args):
    return command('git', *args)


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def git_files(commit, *paths):
    result = {}
    for line in git('ls-tree', '-rz', commit, '--', *paths).split(b'\0'):
        if not line:
            continue
        header, path = line.split(b'\t', 1)
        mode, kind, sha = header.decode().split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            fail('unexpected Git tree entry: ' + path.decode())
        result[path.decode()] = (sha, mode)
    return result


def actual_files(directory):
    if not directory.is_dir():
        fail('missing downloaded data: ' + str(directory))
    found = {}
    for item in directory.rglob('*'):
        if item.is_symlink():
            fail('linked download: ' + str(item))
        if item.is_file():
            relative = item.relative_to(directory).as_posix()
            if relative in found:
                fail('duplicate download name: ' + relative)
            found[relative] = item
    return found


def download_release_output(destination, name):
    destination.mkdir(parents=True, exist_ok=True)
    command('gh', 'run', 'download', RUN_ID, '-R', REPO,
            '--name', name, '--dir', str(destination))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag not in ('a', 'img'):
            return
        properties = dict(attrs)
        key = 'href' if tag == 'a' else 'src'
        if key in properties:
            self.links.append(properties[key])


def verify_galleries(dist):
    pages = [p for p in dist if p.startswith('dist/screenshots/') and p.endswith('/index.html')]
    if 'dist/screenshots/index.html' not in dist or len(pages) != 11:
        fail('missing or unexpected gallery pages')
    for page in pages:
        parser = Links()
        parser.feed(dist[page].read_text(encoding='utf-8'))
        if not parser.links:
            fail('empty gallery links: ' + page)
        for link in parser.links:
            split = urlsplit(link)
            if split.scheme or split.netloc or split.query:
                fail('external or unusual gallery link: ' + page)
            if split.path:
                target = posixpath.normpath(posixpath.join(
                    posixpath.dirname(page), unquote(split.path)))
                if target not in dist:
                    fail('broken gallery link: ' + page + ' -> ' + target)


def verify_capture_pairs(dist):
    for category, count in COMPILERS.items():
        bins = [p for p in dist if p.startswith('dist/assets/' + category + '/')
                and p.endswith('.ssx')]
        if len(bins) != count:
            fail(f'{category}: expected {count} binaries, found {len(bins)}')
        for engine in ('rvm', 'fuse'):
            prefix = 'dist/screenshots/' + category + '/' + engine + '/'
            pictures = [p for p in dist if p.startswith(prefix) and p.endswith('.png')]
            if len(pictures) != CAPTURES[category]:
                fail(f'{category}/{engine}: incorrect screenshot count')
            for name in pictures:
                data = dist[name].read_bytes()
                if not data.startswith(b'\x89PNG\r\n\x1a\n') or data[12:16] != b'IHDR':
                    fail('invalid screenshot header: ' + name)
                import struct
                dimensions = struct.unpack('>II', data[16:24])
                expected = (576, 448) if engine == 'rvm' else (320, 240)
                if dimensions != expected:
                    fail('incorrect screenshot dimensions: ' + name)
        if category == 'rbc-bin':
            for bin_name in bins:
                parts = bin_name.split('/')
                collection, game = parts[3], Path(parts[-1]).stem
                for engine in ('rvm', 'fuse'):
                    screenshot = ('dist/screenshots/rbc-bin/' + engine + '/' +
                                  collection + '/' + game + '.png')
                    if screenshot not in dist:
                        fail('RBC binary missing native screenshot: ' + screenshot)


def verify_release(release, audit_root):
    audit = json.loads((audit_root / 'audit.json').read_text(encoding='utf-8'))
    if audit['head'] != RELEASE_HEAD or audit['unexpected_missing_count'] or \
            audit['unexpected_withheld_count'] or audit['extra_count']:
        fail('clean-room audit failed')
    old_dist = git_files(RELEASE_HEAD, 'dist')
    baseline = git('ls-tree', '-r', RELEASE_HEAD, 'dist')
    if (audit_root / 'baseline.tree').read_bytes() != baseline:
        fail('clean-room audit baseline does not match verified commit')
    missing = set(audit['missing'])
    changed = set(audit['changed'])
    if missing - old_dist.keys() or changed - old_dist.keys() or missing & changed:
        fail('bad distribution changes')
    excluded_pages = {'dist/screenshots/rvm/index.html',
                      'dist/screenshots/fuse/index.html'}
    omissions = set((audit_root / 'capture-omissions.txt').read_text().splitlines())
    if missing != omissions | excluded_pages or omissions & excluded_pages or \
            audit['missing_count'] != len(missing) or \
            audit['changed_count'] != len(changed) or \
            audit['withheld_count'] != len(missing) or \
            audit['rebuilt_file_count'] != len(old_dist) - len(missing):
        fail('unexplained distribution difference')
    codes = audit['stage_exit_codes']
    if set(codes) != set(STAGES) or codes['tests'] != 0:
        fail('clean-room stages incomplete')
    recorded_capture_exits = set((audit_root / 'capture-exits.txt').read_text().splitlines())
    actual_capture_exits = {name for name in ('rbc-rvm', 'rbc-fuse') if codes[name] == 1}
    if recorded_capture_exits != actual_capture_exits or any(
            code for stage, code in codes.items() if stage not in actual_capture_exits):
        fail('unreviewed clean-room failure')
    tests = (audit_root / 'tests.log').read_text(encoding='utf-8')
    if not re.search(r'Ran 69 tests in [\d.]+s\s+OK\b', tests):
        fail('required regression tests did not pass')
    contents = actual_files(release)
    dist = {p: file for p, file in contents.items() if p.startswith('dist/')}
    src = {p: file for p, file in contents.items() if p.startswith('src/')}
    if len(dist) + len(src) != len(contents):
        fail('unrecognized distributed path')
    hidden = {p for p in old_dist if p.endswith('/.gitkeep') and p not in missing}
    if set(dist) != set(old_dist) - missing - hidden or \
            changed & hidden or audit['rebuilt_file_count'] != len(dist) + len(hidden):
        fail('distribution paths differ from completed rebuild')
    found_changed = set()
    for path, file in dist.items():
        actual = git_blob(file.read_bytes())
        if actual != old_dist[path][0]:
            found_changed.add(path)
    if found_changed != changed:
        fail('downloaded binary hashes differ from successful build')

    source_old = git_files(RELEASE_HEAD, *(
        SOURCE + '/' + collection for collection in COLLECTIONS))
    source_old = {p: sha for p, sha in source_old.items() if '/bin/' in p}
    if any(not p.startswith(tuple(SOURCE + '/' + c + '/' for c in COLLECTIONS))
           or '/bin/' not in p for p in src):
        fail('unrecognized source result')
    refused = []
    for line in (audit_root / 'capture-gate.log').read_text().splitlines():
        if line.startswith('REFUSED '):
            words = line.split()
            if len(words) != 3 or words[1] not in COLLECTIONS:
                fail('invalid refused result')
            refused.append((words[1], words[2]))
    if len(refused) != 5 or len(set(refused)) != 5:
        fail('unexpected refused program count')
    deleted = set()
    added = set()
    refusal_bytes = b'# RBC refused\n\nNative RVM and Fuse capture pair was not verified.\n'
    for collection, name in refused:
        folder = SOURCE + '/' + collection + '/' + name + '/bin/'
        ssx = folder + name + '.ssx'
        notice = folder + 'README.md'
        if ssx not in source_old or ssx in src or \
                notice in source_old or notice not in src or \
                src[notice].read_bytes() != refusal_bytes:
            fail('refused native result does not match source archive: ' + name)
        deleted.add(ssx)
        added.add(notice)
    if set(src) != (set(source_old) - deleted) | added:
        fail('extra or missing source result in downloaded output')
    for path in set(src) - added:
        if git_blob(src[path].read_bytes()) != source_old[path][0]:
            fail('accepted native binary modified: ' + path)
    checked_texts = sorted([p for p in changed if p.endswith('.html')] + list(added))
    digest = hashlib.sha256(b''.join(
        p.encode() + b'\0' + (dist if p in dist else src)[p].read_bytes()
        for p in checked_texts)).hexdigest()
    if digest != CHECKED_TEXT_SHA256:
        fail('release text does not match unchanged private checker approval')
    verify_capture_pairs(dist)
    verify_galleries(dist)
    return dist, src, missing, changed, deleted, added


def publish(dist, src, missing, changed, deleted, added):
    if git('status', '--porcelain'):
        fail('checkout not clean')
    git('fetch', 'origin', 'main')
    if git('rev-parse', 'HEAD').strip() != git('rev-parse', 'origin/main').strip():
        fail('remote main moved')
    if git('rev-parse', 'HEAD^').decode().strip() != RELEASE_HEAD:
        fail('publication setup is not based on verified build')
    for path in sorted(missing | deleted):
        target = ROOT / path
        if not target.is_file():
            fail('missing tracked file marked for deletion: ' + path)
        target.unlink()
    for path in sorted(changed | added):
        destination = ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile((dist if path in dist else src)[path], destination)
    git('add', '-A', '--', 'dist')
    git('add', '-A', '--', *(SOURCE + '/' + c for c in COLLECTIONS))
    staged = set(git('diff', '--cached', '--name-only', '-z').decode().rstrip('\0').split('\0'))
    expected = missing | changed | deleted | added
    if staged != expected:
        fail('staged files differ from verified release')
    old = git_files('HEAD', 'dist', *(SOURCE + '/' + c for c in COLLECTIONS))
    expected_shas = dict(old)
    for path in missing | deleted:
        expected_shas.pop(path)
    for path in changed | added:
        expected_shas[path] = (git_blob((dist if path in dist else src)[path].read_bytes()),
                               old[path][1] if path in old else '100644')
    staged_tree = git('write-tree').decode().strip()
    actual = git_files(staged_tree, 'dist', *(SOURCE + '/' + c for c in COLLECTIONS))
    if actual != expected_shas:
        fail('staged Git tree differs from verified release')
    git('fetch', 'origin', 'main')
    if git('rev-parse', 'HEAD').strip() != git('rev-parse', 'origin/main').strip():
        fail('remote main moved before publication')
    command('git', '-c', 'user.name=ZX-UX release runner',
            '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'commit', '-m', MESSAGE)
    if git('rev-parse', 'HEAD^{tree}').decode().strip() != staged_tree:
        fail('new commit tree does not match staged tree')
    if git('rev-parse', 'HEAD^').strip() != git('rev-parse', 'origin/main').strip():
        fail('unexpected commit parent')
    git('push', 'origin', 'HEAD:refs/heads/main')
    git('fetch', 'origin', 'main')
    if (git('rev-parse', 'HEAD').strip() != git('rev-parse', 'origin/main').strip() or
            git('rev-parse', 'HEAD^{tree}').strip() !=
            git('rev-parse', 'origin/main^{tree}').strip()):
        fail('remote publication read-back failed')
    print('PUBLISHED', git('rev-parse', 'HEAD').decode().strip())


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    mode = arg.add_mutually_exclusive_group(required=True)
    mode.add_argument('--verify', action='store_true')
    mode.add_argument('--publish', action='store_true')
    args = arg.parse_args()
    if 'GH_TOKEN' not in os.environ:
        fail('GitHub read token unavailable')
    if git('rev-parse', 'HEAD').decode().strip() == RELEASE_HEAD:
        fail('publisher must run from its own checked-in launcher commit')
    if git('rev-parse', 'HEAD^').decode().strip() != RELEASE_HEAD:
        fail('unexpected publication parent')
    remote = json.loads(command('gh', 'run', 'view', RUN_ID, '-R', REPO,
                                '--json', 'headSha,status,conclusion'))
    if remote['headSha'] != RELEASE_HEAD or remote['status'] != 'completed' or \
            remote['conclusion'] != 'success':
        fail('clean-room workflow not verified successful')
    with tempfile.TemporaryDirectory(prefix='zxux-publish-') as temp:
        root = Path(temp)
        release, audit = root / 'release', root / 'audit'
        download_release_output(release, 'zx-ux-cleanroom-dist')
        download_release_output(audit, 'zx-ux-cleanroom-audit')
        files = verify_release(release, audit)
        print('VERIFIED', 'RBC=96', 'refused=5', 'tests=69', 'images=528')
        if args.publish:
            publish(*files)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print('NOT PUBLISHED:', error, file=sys.stderr)
        raise SystemExit(1)
