"""Fail-closed verification of C48 Rev 0.11 Appendix B public interfaces.

Only declared and implemented public functions count. A kernel service is
not itself a C48 declaration or a callable SDK wrapper. Missing signatures
require verified implementation contracts before any declaration is added.
"""
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'docs/04-C48 Language Specification Rev 0.11.docx'
TEXT = ROOT / 'docs/C48-Language-Spec-Rev011-Standalone.txt'
HEADER = ROOT / 'sdk/include/c48.h'
SPEC_DIGEST = '6368abb4126c01f598f4b533a4e2a0a46a7ce4790cce02d3decbfba59e150d7e'
TEXT_DIGEST = 'd3384e4728dfbfd8d04df5f871afa22a3a7d2bb3dca29cfd645b55f8b9b95563'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    if sha(SPEC) != SPEC_DIGEST or sha(TEXT) != TEXT_DIGEST:
        raise ValueError('Authoritative specification changed; recheck public-name inventory')
    value = TEXT.read_text(encoding='utf-8')
    segment = value.split('Appendix B. Required <c48.h> Public-Name Inventory', 1)[1]
    segment = segment.split('`printf` is not part', 1)[0].split('entries.', 1)[1]
    names = [s.strip() for s in segment.splitlines()
             if re.fullmatch(r'[a-z_][a-z_0-9]*', s.strip())]
    if len(names) != 73 or len(set(names)) != 73:
        raise ValueError('Appendix B public inventory malformed or incomplete')
    return set(names)


def declared(header_text):
    # Only complete, semicolon-terminated public C48 function declarations.
    names = set()
    for line in header_text.splitlines():
        if line.lstrip().startswith(('/*', '*', '//', '#')):
            continue
        m = re.search(r'\b([a-z_][a-z_0-9]*)\s*\([^;{}]*\)\s*;', line)
        if m:
            names.add(m.group(1))
    return names


def implemented():
    exported = set()
    for path in (ROOT / 'sdk/lib').glob('*.asm'):
        for line in path.read_text().splitlines():
            match = re.match(r'^\s*global\s+(.+)$', line)
            if match:
                exported.update(n[1:] for n in match.group(1).split(',')
                                if n.startswith('_') and not n.startswith('__'))
    for path in (ROOT / 'sdk/lib').glob('*.c'):
        body = path.read_text()
        for match in re.finditer(r'(?m)^(?:int|void|char|float|unsigned\s+int|void\s*\*)\s*\*?\s*([a-z_]\w*)\s*\([^;{}]*\)\s*\{', body):
            exported.add(match.group(1))
    return exported


class PublicAPIReleaseChecks(unittest.TestCase):
    def test_inventory_parser_is_strict(self):
        self.assertEqual(len(inventory()), 73)
        self.assertEqual(declared('int alpha(void);\nvoid *beta(int x);'), {'alpha', 'beta'})
        self.assertEqual(declared('int alpha(void)\n#define gamma() 3'), set())

    def test_public_header_and_library_complete(self):
        required = inventory()
        header = declared(HEADER.read_text())
        library = implemented()
        missing_header = sorted(required - header)
        missing_library = sorted(required - library)
        extras = sorted(header - required)
        self.assertFalse(missing_header or missing_library or extras,
                         'Appendix B missing header: %s; missing runtime: %s; extra declarations: %s' %
                         (missing_header, missing_library, extras))


if __name__ == '__main__':
    unittest.main()
