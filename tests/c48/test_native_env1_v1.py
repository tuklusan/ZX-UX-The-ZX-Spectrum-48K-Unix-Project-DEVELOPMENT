"""Fail-closed API and synthetic regression tests. NOT native proof."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

GATE = Path(__file__).with_name('native_env1_v1.py')
spec = importlib.util.spec_from_file_location('env1_release_gate', GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GateBehavior(unittest.TestCase):
    def test_separate_slot_storage_positive(self):
        m=bytearray(65536); base=0x5b44
        m[base:base+4]=bytes([0,0x70,0,0x80]);m[0x7012]=90;m[0x8012]=65
        self.assertEqual(gate.ssx_images(m,0x12),[(0,0x7000,90),(1,0x8000,65)])

    def test_distinct_values_without_distinct_process_ownership_not_proof(self):
        a=(0,0x7000,90);b=(0,0x7000,65)
        self.assertFalse(a[1]!=b[1])

    def test_expected_native_output(self):
        gate.validate_output('# /dev/cassette/env48 e48\nC48-ENV1-OK\n#','C48-ENV1-OK')

    def test_positive_marker_without_failure_not_enough(self):
        with self.assertRaises(gate.GateFailure):
            gate.validate_output('C48-ENV1-OK\nC48-ENV1-FAIL-ALIAS','C48-ENV1-OK')

    def test_missing_marker_stops(self):
        with self.assertRaises(gate.GateFailure):
            gate.validate_output('compiler success only','C48-ENV1-OK')

    def test_missing_source_release_hard_stops(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.object(gate, 'ROOT', Path(t)), patch.object(
                    gate, 'FIXTURE', Path(t) / 'tests/c48/native_env1_storage_lifetime.c'):
                with self.assertRaises(gate.GateFailure):
                    gate.assess_sources()

    def test_no_lib_build_means_fail_not_pass(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t).parent/('native-env1-unit-'+Path(t).name+'.json')
            with patch.object(gate,'ROOT',Path(t)):
                self.assertEqual(gate.main(['--report',str(f),'--tap2sna','/tools/tap2sna.py']),1)
            data=json.loads(f.read_text())
            self.assertEqual(data['result'],'FAIL')
            f.unlink(missing_ok=True)
            self.assertNotIn('native_env1_storage_lifetime',data)

    def test_report_refuses_source_path(self):
        with self.assertRaises(gate.GateFailure):
            gate.main(['--report',str(gate.CRT),'--tap2sna','/tools/tap2sna.py'])

    def test_c48_approved_compiler_is_fixed(self):
        import inspect
        s=inspect.getsource(gate.full_run)
        self.assertIn("SDK_STAGE/'bin/rcc', '--native'",s)
        self.assertIn('archive_env1_symbol',s)
        self.assertIn('consecutive_processes',s)
        self.assertIn('simultaneous_processes',s)
        self.assertNotIn('checker.py',s)


class FakeZX:
    def __init__(self, valid=True):
        self.mem=bytearray(65536)
        self.sim=types.SimpleNamespace(registers=[0]*26)
        self.tr=types.SimpleNamespace(edges=[])
        self.frame=0
        p=0x5b44
        self.mem[p:p+4]=bytes([0,0x70, 0,0x80 if valid else 0x70])
        self.mem[0x700C]=90
        self.mem[(0x8000 if valid else 0x7000)+12]=65 if valid else 90
    def type(self,text):pass
    def run(self,n):self.frame+=n

class FakeSession:
    def __init__(self,snap,valid=True):
        self.zx=FakeZX(valid)
    def login(self): pass
    def until(self,text,frames):pass
    def screen(self):
        return 'C48-ENV1-HOLD-START' if self.zx.frame==0 else ('C48-ENV1-CHECK-OK C48-ENV1-HOLD-OK')
    def wait_prompt(self,frames):pass


class ConcurrentReferenceChecks(unittest.TestCase):
    def run_case(self,valid):
        fake=types.ModuleType('suite')
        fake.Session=lambda snap:FakeSession(snap,valid)
        with patch.dict(sys.modules,{'suite':fake}),\
             patch.object(gate,'df_free',return_value=2000),\
             patch.object(gate,'inject_cassette'),\
             patch.object(gate,'save_capture',return_value={'scr_sha256':'x','png_sha256':'y'}):
            return gate.simultaneous_processes('ignored.z80',[],12)

    def test_distinct_process_images_and_bss_isolation_accept(self):
        result=self.run_case(True)
        self.assertEqual(result['result'],'PASS')
        self.assertEqual(result['simultaneous_image_slots']['hold'],(0,0x7000,90))
        self.assertEqual(result['simultaneous_image_slots']['check'],(1,0x8000,65))

    def test_shared_address_and_single_marker_fail(self):
        with self.assertRaises(gate.GateFailure):self.run_case(False)


class FakeSequentialSession:
    def __init__(self, snap, broken=False):
        self.zx=FakeZX()
        self.broken=broken
        self.n=0
    def login(self):pass
    def wait_prompt(self,frames):self.n+=1
    def screen(self):
        if self.n > 0:
            return ''  # Screen is reclaimed on process exit.
        return 'C48-ENV1-FAIL-ARGV' if self.broken else 'C48-ENV1-OK'


class SequentialReferenceChecks(unittest.TestCase):
    def run_case(self, broken=False, free=None):
        fake=types.ModuleType('suite')
        fake.Session=lambda snap:FakeSequentialSession(snap,broken)
        values=free if free is not None else [3000,2998,2999]
        with patch.dict(sys.modules, {'suite': fake}),\
             patch.object(gate, 'df_free', side_effect=values),\
             patch.object(gate, 'inject_cassette',
                          side_effect=lambda session, *args: setattr(session, 'n', 0)),\
             patch.object(gate, 'save_capture',return_value={'scr_sha256':'a','png_sha256':'b'}):
            return gate.consecutive_processes('ignored.z80',[])

    def test_two_sequential_processes_pass(self):
        cases=self.run_case()
        self.assertEqual(len(cases),2)
        self.assertTrue(all(case['outcome']=='PASS' for case in cases))
        self.assertEqual([case['free_bytes'] for case in cases],[2998,2999])

    def test_negative_c_program_failure_rejected(self):
        with self.assertRaises(gate.GateFailure):self.run_case(broken=True)

    def test_memory_cleanup_regression_rejected(self):
        with self.assertRaises(gate.GateFailure):self.run_case(free=[3000,2950,2950])


class LinkerProofChecks(unittest.TestCase):
    def attempt(self, *, env_offset=9, bss=2, flags=0, needs=500,
                cli=b'NATIVE', symbol=True):
        import types
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'release/build/tmp/sdk/lib').mkdir(parents=True)
            (root/'release/build/tmp/sdk/lib/libc48.ssa').write_bytes(b'ARCHIVE')
            (root/'program.c').write_text('int main(void){return 0;}')
            out=root/'program.ssx';out.write_bytes(cli)
            rld=types.ModuleType('rld')
            rld.Obj=lambda data,name:types.SimpleNamespace(name=name)
            rld.read_archive=lambda data,name:[types.SimpleNamespace(name='member.sso')]
            lookup={'start':(0,True), '@env1':(env_offset, True)}
            if symbol: lookup['__c48_env1']=(env_offset,True)
            rld.link=lambda objs,archives,entry,stack,heap: (
                b'NATIVE',bss,0,lookup,[types.SimpleNamespace(name='crt0.0.sso')])
            rld.parse_ssx=lambda data: {'image':b'12345678','bss':bss,
                 'flags':flags,'entry':0,'stack':384,'heap':0}
            ras=types.ModuleType('ras');ras.assemble_text=lambda src,name:b'ASSEMBLED'
            rtap=types.ModuleType('rtap');rtap.need=lambda data:needs
            pkg=types.ModuleType('rcc');pkg.__path__=[]
            drv=types.ModuleType('rcc.driver')
            drv.compile_to_asm=lambda src,opts:('TEST ASM',None,object())
            drv.stack_estimate=lambda gen:384
            pkg.driver=drv
            with patch.dict(sys.modules,{'rld':rld,'ras':ras,'rtap':rtap,
                                        'rcc':pkg,'rcc.driver':drv}),\
                 patch.object(gate,'ROOT',root), patch.object(gate,'SDK_STAGE',root/'release/build/tmp/sdk'):
                return gate.archive_env1_symbol(root/'program.c',out)

    def test_linked_symbol_in_bss_accepts(self):
        result=self.attempt()
        self.assertEqual(result['env1_bss_offset'],9)
        self.assertEqual(result['ssx_bytes'],6)

    def test_missing_symbol_rejected(self):
        with self.assertRaises(gate.GateFailure):self.attempt(symbol=False)

    def test_symbol_outside_bss_rejected(self):
        with self.assertRaises(gate.GateFailure):self.attempt(env_offset=2)

    def test_bytecode_flag_not_native_rejected(self):
        with self.assertRaises(gate.GateFailure):self.attempt(flags=1)

    def test_native_memory_excess_rejected(self):
        with self.assertRaises(gate.GateFailure):self.attempt(needs=14001)

    def test_cli_and_link_bytes_mismatch_rejected(self):
        with self.assertRaises(gate.GateFailure):self.attempt(cli=b'OTHER')


class FreshSnapshotChecks(unittest.TestCase):
    def run_case(self, *, change_tool=False, save_output=True, stale=False,inside=False):
        import hashlib
        with tempfile.TemporaryDirectory() as t:
            dir=Path(t);root=dir/'checkout';root.mkdir()
            boot=root/'release/dist/zx-ux/ZX-UX.tzx';boot.parent.mkdir(parents=True);boot.write_bytes(b'TZX')
            tool=(root/'private-tap2sna.py') if inside else (dir/'private-tap2sna.py')
            tool.write_bytes(b'good checked tool' if not change_tool else b'wrong tool')
            output=root/'release/build/tmp/build/c48-env1/native-current-tape.z80'
            output.parent.mkdir(parents=True)
            if stale:output.write_bytes(b'STALE OLD SNAPSHOT')
            def runner(cmd):
                if save_output:output.write_bytes(b'new snapshot'*200)
                return 'actual program load'
            with patch.object(gate,'ROOT',root),\
                 patch.object(gate,'TAP2SNA_SHA256',hashlib.sha256(b'good checked tool').hexdigest()),\
                 patch.object(gate,'run',side_effect=runner),\
                 patch.object(gate,'BOOT_TZX',boot),\
                 patch.object(gate,'TMP_BUILD',root/'release/build/tmp/build'):
                return gate.fresh_snapshot(tool)

    def test_snapshot_tape_and_tool_hashes_are_recorded(self):
        out,data=self.run_case()
        self.assertEqual(out.name,'native-current-tape.z80')
        self.assertEqual(data['tape_boot_sha256'],gate.hashlib.sha256(b'TZX').hexdigest())
        self.assertEqual(len(data['snapshot_sha256']),64)

    def test_different_tape_tool_hash_rejected(self):
        with self.assertRaises(gate.GateFailure):self.run_case(change_tool=True)

    def test_stale_snapshot_cannot_substitute_for_fresh(self):
        with self.assertRaises(gate.GateFailure):self.run_case(stale=True,save_output=False)

    def test_missing_new_snapshot_rejected(self):
        with self.assertRaises(gate.GateFailure):self.run_case(save_output=False)

    def test_private_tool_cannot_live_inside_git(self):
        with self.assertRaises(gate.GateFailure):self.run_case(inside=True)


if __name__=='__main__':unittest.main()
