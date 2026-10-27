"""Locked full-program optimizer inputs must work without online downloads."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stage'))
from gate8_offline_inputs import (verified_zip_sources, prepare_offline,
                                  OfflineInputsError)
from hisoft_frontend_inputs import git_blob


class OfflineLockedInputsTests(unittest.TestCase):
    def test_exact_locked_source_from_arbitrary_archive_root(self):
        text = b'correct upstream contents\n'
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'sources.zip'
            with ZipFile(archive, 'w') as z:
                z.writestr('snapshot-upstream/pkg/code.py', text)
            self.assertEqual(verified_zip_sources(archive, 'pkg/',
                            {'code.py': git_blob(text)}), {'code.py': text})

    def test_modified_or_ambiguous_blob_is_rejected(self):
        text = b'locked upstream contents\n'
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'sources.zip'
            with ZipFile(archive, 'w') as z:
                z.writestr('snapshot/pkg/code.py', text + b'modified')
            with self.assertRaisesRegex(OfflineInputsError, 'Git blob mismatch'):
                verified_zip_sources(archive, 'pkg/', {'code.py': git_blob(text)})
            with self.assertRaisesRegex(OfflineInputsError, 'missing or duplicate'):
                verified_zip_sources(archive, 'pkg/', {'other.py': git_blob(text)})
            with ZipFile(archive, 'w') as z:
                z.writestr('snapshot/pkg/code.py', text)
                z.writestr('another/pkg/code.py', text)
            with self.assertRaisesRegex(OfflineInputsError, 'duplicate'):
                verified_zip_sources(archive, 'pkg/', {'code.py': git_blob(text)})

    def test_cross_snapshot_and_traversal_paths_are_rejected(self):
        a, b = b'a', b'b'
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'sources.zip'
            with ZipFile(archive, 'w') as z:
                z.writestr('snapshot/pkg/a.py', a)
                z.writestr('other/pkg/b.py', b)
            with self.assertRaisesRegex(OfflineInputsError, 'different trees'):
                verified_zip_sources(archive, 'pkg/',
                                     {'a.py': git_blob(a), 'b.py': git_blob(b)})
            with ZipFile(archive, 'w') as z:
                z.writestr('../snapshot/pkg/a.py', a)
            with self.assertRaisesRegex(OfflineInputsError, 'unsafe'):
                verified_zip_sources(archive, 'pkg/', {'a.py': git_blob(a)})

    def test_full_local_inputs_with_locked_upstream_archives(self):
        names = ('RBC_G8_FRONTEND_ARCHIVE', 'RBC_G8_OPTIMIZER_ARCHIVE',
                 'RBC_G8_COMPILER_TZX')
        files = [os.environ.get(name) for name in names]
        if not all(files):
            self.skipTest('requires three exact offline sources')
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'sources'
            env = prepare_offline(ROOT, *map(Path, files), out)
            self.assertTrue((Path(env['RBC_G8_CHECKPOINT']) / 'rbc.py').is_file())
            self.assertEqual(len(list(Path(env['RBC_G8_FRONTEND']).glob('*.py'))), 11)
            self.assertEqual(len(list((Path(env['RBC_G8_OPTIMIZER']) / 'upeepz80').glob('*.py'))), 3)
            self.assertEqual(env['tape_sha256'],
                             hashlib.sha256(Path(env['RBC_G8_TAPE']).read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                prepare_offline(ROOT, *map(Path, files), out)


if __name__ == '__main__':
    unittest.main()
