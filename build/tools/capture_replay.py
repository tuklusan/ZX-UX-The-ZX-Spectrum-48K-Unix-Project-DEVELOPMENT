"""Read recorded BASIC gameplay steps as data; never execute archive REPLAY.sh."""
from __future__ import annotations

from pathlib import Path
import json
import re

COLLECTIONS = (Path(__file__).resolve().parents[2] / 'src/assets/basic-src'
               / 'original-sinclair-basic-collections')
SCRIPT = re.compile(r'^Recorded ordered script:\s*(.+?)\s*$', re.M)
_ALLOWED = re.compile(r'^[\x20-\x7e]{1,60}$')
RECORDED = Path(__file__).with_name('rbc_replays.json')


def parse_script(script: str, origin: str):
    """Read explicitly recorded actions; refuse malformed controls."""
    result = []
    for token in script.split('|'):
        parts = token.split(':')
        kind = parts[0]
        if kind in ('K', 'S', 'L') and len(parts) == 2 and _ALLOWED.fullmatch(parts[1]):
            result.append((kind, parts[1]))
        elif kind == 'H' and len(parts) == 3 and _ALLOWED.fullmatch(parts[1]):
            try:
                seconds = float(parts[2])
            except ValueError:
                raise ValueError('invalid recorded hold in ' + origin) from None
            if not 0 < seconds <= 4:
                raise ValueError('invalid recorded hold in ' + origin)
            result.append((kind, parts[1], seconds))
        elif kind == 'W' and len(parts) == 2:
            try:
                seconds = float(parts[1])
            except ValueError:
                raise ValueError('invalid recorded wait in ' + origin) from None
            if not 0 < seconds <= 30:
                raise ValueError('invalid recorded wait in ' + origin)
            result.append((kind, seconds))
        elif kind == 'C' and len(parts) == 2 and _ALLOWED.fullmatch(parts[1]):
            result.append((kind, parts[1]))
        else:
            raise ValueError('unrecognized recorded BASIC step in ' + origin + ': ' + token)
    return tuple(result)


def steps(collection: str, game: str):
    """Use only recorded actions; ROM BASIC results are not native proof."""
    directory = COLLECTIONS / collection / game / 'BASIC'
    if not directory.is_dir():
        return ()
    guides = [p for p in directory.iterdir() if p.name.lower() == 'keys-and-timing.txt']
    if len(guides) != 1:
        return ()
    guide = guides[0]
    match = SCRIPT.search(guide.read_text(encoding='utf-8'))
    recorded = json.loads(RECORDED.read_text(encoding='utf-8')) if RECORDED.is_file() else {}
    name = collection + '/' + game
    if not isinstance(recorded, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                              for k, v in recorded.items()):
        raise ValueError('invalid project-owned replay data')
    if name in recorded and match:
        raise ValueError('conflicting recorded replay data: ' + name)
    if name in recorded:
        return parse_script(recorded[name], str(RECORDED))
    return parse_script(match.group(1), str(guide)) if match else ()


def key(name: str):
    """Convert the archive's X11 key name into a Spectrum keystroke."""
    return {'space': ' ', 'Return': '\n', 'Enter': '\n'}.get(name, name)


def rvm_actions(recorded):
    """Convert measured key presses into RVM keyboard scans (50 per second)."""
    import zxux
    actions = [('wait', 45)]
    for item in recorded:
        kind = item[0]
        if kind == 'W':
            actions.append(('wait', max(1, round(item[1] * 50))))
            continue
        if kind == 'C':
            actions.append(('wait', 30))
            continue
        if kind == 'L':
            sequence = item[1] + '\n'
        elif kind == 'S':
            sequence = item[1].upper()
        else:
            sequence = key(item[1])
        for action in zxux.parse_keys(sequence):
            if kind == 'H' and action[0] == 'keys':
                actions.append(('press', action[1], max(1, round(item[2] * 50))))
            else:
                actions.append(action)
            actions.append(('wait', 7))
        actions.append(('wait', 40))
    return actions


def fuse_steps(recorded):
    """Existing Fuse runner input tuples: (delay,text) or (delay,key,hold)."""
    result = []
    for item in recorded:
        kind = item[0]
        if kind == 'W':
            result.append((item[1], ''))
        elif kind == 'C':
            result.append((0.5, ''))
        elif kind == 'L':
            result.append((0.65, item[1] + '\n'))
        elif kind == 'S':
            result.append((0.65, item[1].upper()))
        elif kind == 'K':
            result.append((0.65, key(item[1])))
        else:
            result.append((0.65, key(item[1]), item[2]))
    return result
