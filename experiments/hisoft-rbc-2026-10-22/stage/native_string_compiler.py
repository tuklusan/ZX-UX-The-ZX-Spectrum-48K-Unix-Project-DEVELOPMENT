"""Implement proven scalar text lengths directly in the Python native backend.

No extra BASIC line numbers or alterations to the saved input are necessary.
"""


def with_static_strings(base, proofs, letter):
    capacities = []
    for entry in proofs:
        name = entry['variable']
        limit = entry['max_chars']
        if (not isinstance(name, str) or len(name) != 2 or name[1] != '$'
                or not name[0].isalpha() or not name[0].isascii()
                or not isinstance(limit, int) or not 1 <= limit <= 13000
                or (limit > 255 and (limit != 664 or entry.get("bound_proof") !=
                    "original-exocet-bounded-concatenation"))):
            raise ValueError('invalid static text capacity')
        capacities.append((name[0].lower(), limit))
    if len({n for n, _ in capacities}) != len(capacities):
        raise ValueError('duplicate text-capacity assignment')
    if not capacities:
        return base

    class StaticTextCompiler(base):
        def reset(self, program):
            super().reset(program)
            for name, capacity in capacities:
                entry = self.strvars[letter(ord(name))]
                if entry['flags'] or entry['first'] or entry['last']:
                    raise ValueError('text capacity conflicts with existing declaration')
                entry['last'] = capacity

    return StaticTextCompiler
