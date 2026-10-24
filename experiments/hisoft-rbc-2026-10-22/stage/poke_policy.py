"""Dynamic POKE is the program's responsibility, unless danger is proved."""


class ProtectedPoke(ValueError):
    pass


def apply_poke_policy(findings, proofs):
    by_line = {}
    for item in proofs:
        by_line.setdefault(item['line'], []).append(item)
    for finding in findings:
        if finding.operation != 'POKE':
            continue
        matched = by_line.get(finding.line, [])
        if not matched:
            raise ProtectedPoke(f'Line {finding.line}: POKE token check mismatch')
        proof = matched.pop(0)
        locations = proof.get('addresses', [])
        for target in locations:
            location = target['offset']
            if target['space'] == 'process_udg':
                if not 0 <= location < 168:
                    raise ProtectedPoke(f'Line {finding.line}: UDG offset {location} outside 0..167')
            elif target['space'] != 'absolute' or not 0x4000 <= location <= 0x5AFF:
                raise ProtectedPoke(f'Line {finding.line}: POKE {location} targets protected machine state')
        finding.severity = 'info' if locations and all(
            x['space'] == 'process_udg' for x in locations) else 'review'
        finding.classification = ('bounded_process_udg_write' if finding.severity == 'info'
                                  else 'program_responsibility_poke')
    if any(by_line.values()):
        raise ProtectedPoke('POKE token/proof count mismatch')