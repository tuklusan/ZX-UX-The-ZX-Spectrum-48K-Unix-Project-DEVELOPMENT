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


def _recorded():
    data = json.loads(RECORDED.read_text(encoding='utf-8')) if RECORDED.is_file() else {}
    if not isinstance(data, dict):
        raise ValueError('invalid project-owned replay data')
    for name, entry in data.items():
        if not isinstance(name, str):
            raise ValueError('invalid recorded replay identifier')
        if isinstance(entry, str):
            continue
        if (not isinstance(entry, dict)
                or set(entry) != {'script', 'require_change'}
                or not isinstance(entry['script'], str)
                or not isinstance(entry['require_change'], bool)):
            raise ValueError('invalid project-owned replay metadata: ' + name)
    return data


def replay_requires_change(collection: str, game: str) -> bool:
    """Require a changed post-key screen only when recorded by this recipe."""
    entry = _recorded().get(collection + '/' + game)
    return isinstance(entry, dict) and entry['require_change']


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
    recorded = _recorded()
    name = collection + '/' + game
    if name in recorded and match:
        raise ValueError('conflicting recorded replay data: ' + name)
    if name in recorded:
        recipe = recorded[name]
        return parse_script(recipe['script'] if isinstance(recipe, dict) else recipe,
                            str(RECORDED))
    return parse_script(match.group(1), str(guide)) if match else ()



def recorded_first_input_wait(collection: str, game: str, recorded) -> int | None:
    """Native scan delay from the original, measured FUSE input-event record.

    Only apply a recorded delay when the next event agrees with the first
    gameplay key in the ordered recipe. Never run the archive's shell scripts.
    """
    directory = COLLECTIONS / collection / game / 'BASIC'
    guides = list(directory.glob('[Kk][Ee][Yy][Ss]-[Aa][Nn][Dd]-[Tt][Ii][Mm][Ii][Nn][Gg].[Tt][Xx][Tt]')) if directory.is_dir() else []
    if len(guides) != 1 or not any(item[0] == 'C' for item in recorded):
        return None
    source = guides[0].read_text(encoding='utf-8')
    if 'EXACT INPUT EVENTS' not in source or 'SELECTED SCREENSHOTS' not in source:
        return None
    block = source.split('EXACT INPUT EVENTS', 1)[1].split('SELECTED SCREENSHOTS', 1)[0]
    events = re.findall(r'^\s*(\d+\.\d+)\s+s\s+(\S+)\s*$', block, re.M)
    returns = [index for index, (_, key_name) in enumerate(events) if key_name == 'Return']
    first = next((item for item in recorded if item[0] in ('K', 'H', 'L', 'S')), None)
    if first is None or len(returns) < 2 or returns[1] + 1 >= len(events):
        return None
    expected = first[1][0] if first[0] in ('L', 'S') else first[1]
    seconds, actual = events[returns[1] + 1]
    if actual.casefold() != expected.casefold():
        return None
    delay = float(seconds) - float(events[returns[1]][0])
    return round(delay * 50) if 0 < delay <= 30 else None

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
