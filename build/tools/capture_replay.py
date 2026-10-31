"""Read recorded BASIC gameplay steps as data; never execute archive REPLAY.sh."""
from __future__ import annotations

from pathlib import Path
import re

COLLECTIONS = (Path(__file__).resolve().parents[2] / 'src/assets/basic-src'
               / 'original-sinclair-basic-collections')
SCRIPT = re.compile(r'^Recorded ordered script:\s*(.+?)\s*$', re.M)
_ALLOWED = re.compile(r'^[\x20-\x7e]{1,60}$')


def steps(collection: str, game: str):
    """Return documented ('K'|'H'|'L'|'S'|'C', ...) actions, or empty if absent.

    The original replay targets ROM BASIC. These are candidate controls for the
    separately compiled native program, not a claim of equivalent gameplay.
    """
    directory = COLLECTIONS / collection / game / 'BASIC'
    if not directory.is_dir():
        return ()
    guides = [p for p in directory.iterdir() if p.name.lower() == 'keys-and-timing.txt']
    if len(guides) != 1:
        return ()
    match = SCRIPT.search(guides[0].read_text(encoding='utf-8'))
    if not match:
        return ()
    result = []
    for token in match.group(1).split('|'):
        parts = token.split(':')
        kind = parts[0]
        if kind in ('K', 'S', 'L') and len(parts) == 2 and _ALLOWED.fullmatch(parts[1]):
            result.append((kind, parts[1]))
        elif kind == 'H' and len(parts) == 3 and _ALLOWED.fullmatch(parts[1]) and 0 < float(parts[2]) <= 4:
            result.append((kind, parts[1], float(parts[2])))
        elif kind == 'C' and len(parts) == 2 and _ALLOWED.fullmatch(parts[1]):
            result.append((kind, parts[1]))
        else:
            raise ValueError('unrecognized recorded BASIC step in ' + str(guides[0]) + ': ' + token)
    return tuple(result)


def key(name: str):
    """Convert the archive's X11 key name into a Spectrum keystroke."""
    return {'space': ' ', 'Return': '\n', 'Enter': '\n'}.get(name, name)


def rvm_actions(recorded):
    """Convert measured key presses into RVM keyboard scans (50 per second)."""
    import zxux
    actions = [('wait', 45)]
    for item in recorded:
        kind = item[0]
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
        if kind == 'C':
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
