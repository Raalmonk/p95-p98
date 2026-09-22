import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest import mock
from p95p98.promod.input import prepare_source
from p95p98.promod.mapping import map_output_lines, sequence_coverage
from p95p98.promod.errors import PreparationPending
from p95p98.promod.native import ProModNative, verify_source_exclusion
from p95p98.promod.runner import execute


def pdb_line(serial, atom, residue, number, chain='X'):
    return f'ATOM  {serial:5d} {atom:>4} {residue:>3} {chain}{number:4d}    {0.:8.3f}{0.:8.3f}{0.:8.3f}  1.00  0.00          {atom[0]:>2}\n'


class ProModTests(unittest.TestCase):
    def test_new_input_gap_and_mapping_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            lines=[pdb_line(i*4+j+1,a,r,i+10) for i,r in enumerate(['ALA','GLY','VAL','LYS'])
                   for j,a in enumerate(['N','CA','C','O'])]
            (root/'in.pdb').write_text(''.join(lines)+'TER\nEND\n')
            path=prepare_source(root/'in.pdb','AGVK',[{'start':2,'stop':3}],root/'converted')
            data=json.loads(path.read_text())
            self.assertEqual(data['segments'][0]['aligned_source'],'A--K')
            self.assertEqual(data['segments'][0]['indices'],[1,2,3,4])
            content=(path.parent/'source.pdb').read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(),data['source_pdb_sha256'])
            self.assertEqual(content.count(b'ATOM'),8)
            native=[pdb_line(i+1,'CA',r,i+1,chain='A') for i,r in enumerate(['ALA','GLY','VAL','LYS'])]
            mapped=map_output_lines(native,data)
            self.assertEqual([s[21] for s in mapped],['X']*4)
            self.assertEqual([int(s[22:26]) for s in mapped],[1,2,3,4])
            self.assertEqual([s[30:] for s in mapped],[s[30:] for s in native])
            with self.assertRaises(PreparationPending):
                map_output_lines(native[:-1],data)

    def test_reject_sequence_change_and_terminal_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source.pdb'
            source.write_text(''.join(pdb_line(i*4+j+1,a,'ALA',i+1)
                for i in range(3) for j,a in enumerate(['N','CA','C','O'])))
            for sequence, loops in [('AGA',[{'start':2,'stop':2}]),('AAA',[{'start':1,'stop':2}])]:
                with self.assertRaises(ValueError):
                    prepare_source(source,sequence,loops,root/'out')

    def test_original_finalization_order_and_partial_delivery(self):
        calls=[]
        modelling=NS(ReconstructSidechains=lambda *a,**kw:calls.append(('sidechain',kw)),
            GetRings=lambda *a:[], GetRingPunches=lambda *a:[],
            MinimizeModelEnergy=lambda *a:calls.append(('minimize',{})),
            CheckFinalModel=lambda *a:calls.append(('check',{})))
        adapter=object.__new__(ProModNative)
        adapter.modelling=modelling; adapter.events=[]; adapter.checkpoint=lambda *a:None
        handle=NS(model=object(),gaps=[1])
        self.assertEqual(adapter.finish_without_gap_search(handle,rotamer_library=None)['status'],'PARTIAL_MODEL')
        self.assertEqual(calls,[])
        handle.gaps=[]
        result=adapter.finish_without_gap_search(handle,rotamer_library=None)
        self.assertEqual(result['status'],'MODEL_RETURNED')
        self.assertEqual([v[0] for v in calls],['sidechain','minimize','check'])
        self.assertIs(calls[0][1]['keep_sidechains'],True)

    def test_missing_resources_explicit(self):
        with self.assertRaises(PreparationPending):
            ProModNative(modelling=None,loop=None,sidechain=None,io=None,seq=None,
                         input_root='.',database_receipt={},verified_resources={})

    def test_resource_ledger_protects_actual_input(self):
        data=dict(segments=[dict(sequence='ACD'),dict(sequence='EFG')],expected_sequence='ACDEFG')
        verify_source_exclusion(data,dict(protected=dict(sequences=[dict(sequence='ACDEFG')])))
        for sequences in ([],[dict(sequence='ACD')],[dict(sequence='AAAAAA')]):
            with self.assertRaises(PreparationPending):
                verify_source_exclusion(data,dict(protected=dict(sequences=sequences)))

    def test_sigkill_is_not_inferred_cpu_limit(self):
        import signal
        for sig, expected in ((signal.SIGKILL,'KILLED_UNKNOWN_CAUSE'),(signal.SIGXCPU,'CPU_LIMIT')):
            with tempfile.TemporaryDirectory() as tmp, mock.patch('p95p98.promod.runner.subprocess.Popen') as popen, \
                    mock.patch('p95p98.promod.runner.os.wait4',return_value=(123,int(sig),NS(ru_utime=20.,ru_stime=2.))):
                popen.return_value.pid=123
                result=execute('input.json','promod3_database',tmp,'resources.json',['python'],20.,100.)
                self.assertEqual(result['status'],expected)
                self.assertEqual(result['physical_cpu_seconds'],22.)


if __name__=='__main__':
    unittest.main()
