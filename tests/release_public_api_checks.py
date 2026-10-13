"""Verify the 52 required public names and the approved kernel API additions.

Appendix B stays normative; extra names are kernel interfaces and are
verified here separately rather than silently treated as Appendix B entries.
"""
import hashlib
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'docs/04-C48 Language Specification Rev 0.11.docx'
HEADER = ROOT / 'sdk/include/c48.h'
SPEC_DIGEST = '6368abb4126c01f598f4b533a4e2a0a46a7ce4790cce02d3decbfba59e150d7e'
TITLE = 'Appendix B. Required <c48.h> Public-Name Inventory'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def inventory():
    """Read Appendix B directly from the authoritative DOCX, not a text copy."""
    if hashlib.sha256(SPEC.read_bytes()).hexdigest() != SPEC_DIGEST:
        raise ValueError('Specification identity differs')
    with zipfile.ZipFile(SPEC) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    t = '{' + NS['w'] + '}'
    paragraphs = []
    for p in root.findall('./w:body/w:p', NS):
        fields = []
        for node in p.iter():
            if node.tag == t + 't' and node.text:
                fields.append(node.text)
            elif node.tag in (t + 'br', t + 'cr'):
                fields.append('\n')
        paragraphs.append(''.join(fields).strip())
    if paragraphs.count(TITLE) != 1:
        raise ValueError('Ambiguous public-name appendix')
    index = paragraphs.index(TITLE)
    if index + 2 >= len(paragraphs) or 'Missing historical facilities are not v1 promises.' not in paragraphs[index + 1]:
        raise ValueError('Public-name amendment is missing')
    names = [x.strip() for x in paragraphs[index + 2].splitlines()]
    if len(names) != 52 or len(set(names)) != 52 or not all(
        re.fullmatch(r'[a-z_][a-z_0-9]*', x) for x in names
    ):
        raise ValueError('Invalid 52-name Appendix B inventory')
    return set(names)


def declared(header_text):
    names = set()
    for line in header_text.splitlines():
        if line.lstrip().startswith(('/*', '*', '//', '#')):
            continue
        match = re.search(r'\b([a-z_][a-z_0-9]*)\s*\([^;{}]*\)\s*;', line)
        if match:
            names.add(match.group(1))
    return names


def implemented():
    exported = set()
    for path in (ROOT / 'sdk/lib').glob('*.asm'):
        for line in path.read_text().splitlines():
            match = re.match(r'^\s*global\s+(.+)$', line)
            if match:
                exported.update(name[1:] for name in match.group(1).split(',')
                                if name.startswith('_') and not name.startswith('__'))
    for path in (ROOT / 'sdk/lib').glob('*.c'):
        for match in re.finditer(
            r'(?m)^(?:int|void|char|float|unsigned\s+int|void\s*\*)\s*\*?\s*([a-z_]\w*)\s*\([^;{}]*\)\s*\{',
            path.read_text(),
        ):
            exported.add(match.group(1))
    return exported


def missing_names(required, header, library):
    return (sorted(required - header), sorted(required - library), sorted(header - required))


class PublicAPIReleaseChecks(unittest.TestCase):
    def test_appendix_inventory_is_exact(self):
        self.assertEqual(len(inventory()), 52)
        self.assertEqual(declared('int alpha(void);\nvoid *beta(int x);'), {'alpha', 'beta'})
        self.assertEqual(declared('int alpha(void)\n#define gamma() 3'), set())
        self.assertEqual(missing_names({'one', 'two'}, {'one'}, {'two'}),
                         (['two'], ['one'], []))

    def test_header_and_library_match_current_appendix(self):
        required = inventory()
        # These are the additional kernel syscall wrappers explicitly requested
        # for the independent SDK. They do not change the 52-name Appendix B.
        additional_kernel_api = {
            'brk', 'cemt', 'chdir', 'chmod', 'chown', 'creat', 'exec',
            'fork', 'fstat', 'getuid', 'gtty', 'ilgins', 'intr', 'kill',
            'link', 'lseek', 'mdate', 'mkdir', 'quit', 'screen', 'setuid',
            'ssxload', 'stat', 'stime', 'stty', 'tell', 'time', 'unlink',
            'wait', 'write', 'zxinfo', 'zxpack',
        }
        header = declared(HEADER.read_text())
        library = implemented()
        self.assertEqual(missing_names(required, header, library),
                         ([], [], sorted(additional_kernel_api)))
        self.assertEqual(additional_kernel_api - library, set())
        self.assertEqual(header - required, additional_kernel_api)



if __name__ == '__main__':
    unittest.main()
