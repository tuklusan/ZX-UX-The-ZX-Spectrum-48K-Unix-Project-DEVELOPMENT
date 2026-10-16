"""Fail-closed independent native ENV1 proof acceptance, using synthetic files.

These are unit tests of proof validation; a generated record is NOT native proof.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
from PIL import Image

HERE = Path(__file__).resolve().parent
modspec = importlib.util.spec_from_file_location('c48_target_gate', HERE / 'target_gate.py')
gate = importlib.util.module_from_spec(modspec)
modspec.loader.exec_module(gate)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class NativeProofChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write('release/build/tmp/sdk/lib/libc48.ssa', b'SSA1 synthetic unit file')
        self.write('release/build/tmp/build/c48-env1/env48.ssx', b'SSX1 synthetic unit file')
        self.write('release/build/tmp/build/c48-env1/native-current-tape.z80', b'fake snapshot')
        for name in gate.ENV1_INPUTS:
            self.write(name, ('fixture: ' + name + '\n').encode())
        subprocess.run(['git','init','-q'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=Test', '-c','user.email=test@example.invalid',
                        'add','--all'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=Test', '-c','user.email=test@example.invalid',
                        'commit','-q','-m','Local synthetic unit fixtures'],cwd=self.root,check=True)
        source = {'source_commit':self.git('HEAD'), 'source_tree':self.git('HEAD^{tree}'),
                  'files':{name:sha((self.root/name).read_bytes()) for name in gate.ENV1_INPUTS}}
        link = {'ssx_sha256':sha((self.root/'release/build/tmp/build/c48-env1/env48.ssx').read_bytes()),
                'ssx_bytes':len((self.root/'release/build/tmp/build/c48-env1/env48.ssx').read_bytes()),
                'archive_sha256':sha((self.root/'release/build/tmp/sdk/lib/libc48.ssa').read_bytes()),
                'code':24,'bss':3,'env1_bss_offset':24,'native_required_bytes':8000,
                'selected_archive_members':['crt0']}
        snapshot = {'tap2sna_sha256':gate.TAP2SNA_SHA256,
                    'rom_sha256':gate.ROM_SHA256,
                    'tape_boot_sha256':source['files']['release/dist/zx-ux/ZX-UX.tzx'],
                    'snapshot_sha256':sha((self.root/'release/build/tmp/build/c48-env1/native-current-tape.z80').read_bytes())}
        records = []
        for i in (1,2):
            records.append({'run':i,'outcome':'PASS','free_bytes':4000,
                            'screen_sha256':sha(b'characters'),
                            'capture':self.capture('sequential-'+str(i))})
        concurrent = {'result':'PASS', 'checked_program_pass':True,
                      'holding_program_pass':True,
                      'simultaneous_image_slots':{'hold':[0,24576,90], 'check':[1,25000,65]},
                      'capture':self.capture('concurrent')}
        self.proof={'result':'PASS', 'case_id':'native_env1_storage_lifetime',
                    'compiler':'release/build/tmp/sdk/bin/rcc --native', 'target':'ZX-UX v1 native',
                    'source':source, 'link':link, 'native_snapshot':snapshot,
                    'sequential':records, 'concurrent':concurrent,
                    'runtime_build_log_sha256':sha(b'runtime output'),
                    'compiler_log_sha256':sha(b'compiler output')}

    def write(self, name, contents):
        path=self.root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(contents)

    def git(self, spec):
        return subprocess.check_output(['git','rev-parse',spec],cwd=self.root,text=True).strip()

    def capture(self, basename):
        scr='release/build/tmp/build/c48-env1/proof/'+basename+'.scr'
        png='release/build/tmp/build/c48-env1/proof/'+basename+'.png'
        self.write(scr, bytes(6912))
        image_path=self.root/png
        image_path.parent.mkdir(parents=True,exist_ok=True)
        Image.new('RGB',(256,192)).save(image_path)
        return {'scr_path':scr,'scr_sha256':sha((self.root/scr).read_bytes()),
                'png_path':png,'png_sha256':sha(image_path.read_bytes())}

    def rejected(self, proof):
        with self.assertRaises(ValueError):
            gate.verify_native_env1(proof,self.root)

    def test_validated_report_shape_with_local_test_inputs(self):
        self.assertTrue(gate.verify_native_env1(self.proof,self.root))

    def test_static_abi_matrix_clears_only_with_validated_native_witness(self):
        matrix=json.loads((HERE/'matrix.json').read_text())
        verifier={'backend':'both', 'cases':[{'id':c,'status':'PASS'} for c in sorted({c for r in matrix['rows'] for c in r['passing_cases']})]}
        verifier['summary']={'PASS':len(verifier['cases']), 'FAIL':0, 'ERROR':0}
        for row in matrix['rows']:
            for path in row['source_paths']:
                staged = ('release/src/zx-ux-sdk/' + path[4:]
                          if path.startswith('sdk/') else path)
                if not (self.root/staged).is_file():
                    self.write(staged, b'synthetic source fixture')
        # A synthetic IX report exercises gate routing, not hardware.
        self.write('release/src/zx-ux-sdk/lib/frame.asm',b'synthetic frame fixture')
        ix={'name':'native_ix_register_preservation_8_cases', 'result':'PASS', 'count':8,
            'frame_sha256':sha((self.root/'release/src/zx-ux-sdk/lib/frame.asm').read_bytes()),
            'cases':[{'ix':a,'stack':b} for a in (0,1,0xA55A,0xFFFF)
                     for b in (0xE000,0xF000)]}
        missing=gate.assess(matrix,verifier,ix,root=self.root)
        self.assertEqual(missing['unresolved'],[1080])
        with mock.patch.object(gate,'verify_native_env1',return_value=True) as accepted:
            completed=gate.assess(matrix,verifier,ix,root=self.root,
                                  env1_proof=self.proof)
        accepted.assert_called_once()
        self.assertEqual(completed['unresolved'],[])

    def test_missing_proof_rejected(self):
        self.rejected(None)

    def test_failure_record_rejected(self):
        x=copy.deepcopy(self.proof);x['result']='FAIL';self.rejected(x)

    def test_changed_source_commit_rejected(self):
        x=copy.deepcopy(self.proof);x['source']['source_commit']='0'*40;self.rejected(x)

    def test_changed_source_bytes_rejected(self):
        self.write('release/src/zx-ux-sdk/lib/crt0.asm',b'changed source');self.rejected(self.proof)

    def test_archived_runtime_mismatch_rejected(self):
        self.write('release/build/tmp/sdk/lib/libc48.ssa',b'changed runtime');self.rejected(self.proof)

    def test_boot_tape_not_current_rejected(self):
        self.write('release/dist/zx-ux/ZX-UX.tzx',b'changed tape');self.rejected(self.proof)

    def test_missing_sequential_run_rejected(self):
        x=copy.deepcopy(self.proof);x['sequential'].pop();self.rejected(x)

    def test_concurrent_same_process_rejected(self):
        x=copy.deepcopy(self.proof);x['concurrent']['simultaneous_image_slots']['check'][0]=0;self.rejected(x)

    def test_concurrent_unobserved_rejected(self):
        x=copy.deepcopy(self.proof);x['concurrent']['checked_program_pass']=False;self.rejected(x)

    def test_missing_capture_rejected(self):
        (self.root/'release/build/tmp/build/c48-env1/proof/concurrent.scr').unlink();self.rejected(self.proof)

    def test_oversized_native_rejected(self):
        x=copy.deepcopy(self.proof);x['link']['native_required_bytes']=14001;self.rejected(x)

    def test_wrong_linked_bss_rejected(self):
        x=copy.deepcopy(self.proof);x['link']['env1_bss_offset']=20;self.rejected(x)

    def test_old_tape_loader_rejected(self):
        x=copy.deepcopy(self.proof);x['native_snapshot']['tap2sna_sha256']='0'*64;self.rejected(x)
    def test_wrong_rom_rejected(self):
        x=copy.deepcopy(self.proof);x['native_snapshot']['rom_sha256']='0'*64;self.rejected(x)


    def test_bad_screenshot_bytes_rejected(self):
        self.write('release/build/tmp/build/c48-env1/proof/concurrent.png',b'not a PNG');self.rejected(self.proof)


if __name__ == '__main__':
    unittest.main()
