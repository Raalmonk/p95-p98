"""Receipt and rejection boundary unit tests, without native calculations."""
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from p95p98.runner import chemistry_check, command_identity, failure_charge


class RunnerAccountingTests(unittest.TestCase):
    def test_candidate_chemistry_rejected_but_integrity_error_propagates(self):
        def fail(message):
            def compatible(pose):
                raise ValueError(message)
            return SimpleNamespace(compatible=compatible)
        result=chemistry_check(fail('Candidate topology differs from frozen source'),None)
        self.assertEqual(result['status'],'INCOMPATIBLE')
        self.assertGreaterEqual(result['cpu_seconds'],0)
        with self.assertRaisesRegex(ValueError,'Source contract changed'):
            chemistry_check(fail('Source contract changed'),None)
        self.assertEqual(chemistry_check(SimpleNamespace(compatible=lambda pose: []),None)['status'],
                         'COMPATIBLE')

    def test_failed_controlled_work_preserves_independent_logical_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'native').mkdir()
            (folder/'native/exit.json').write_text(json.dumps({'cpu_seconds':7.,'status':'ERROR'}))
            cap=SimpleNamespace(name='ngk_refine',logical_work=30.)
            self.assertEqual(failure_charge(cap,folder)['logical_work'],30.)
            (folder/'logical_progress.json').write_text(json.dumps({'work':12.}))
            record=failure_charge(cap,folder)
            self.assertEqual(record['logical_work'],12.)
            self.assertEqual(record['cpu_seconds'],7.)
            with gzip.open(folder/'native/returned.json.gz','wt') as f:
                json.dump({'work':15.},f)
            self.assertEqual(failure_charge(cap,folder)['logical_work'],15.)
            (folder/'native/returned.json.gz').unlink()
            (folder/'logical_progress.json').write_text(json.dumps({'work':45.}))
            self.assertEqual(failure_charge(cap,folder)['logical_work'],30.)

    def test_failed_database_cost_and_missing_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);cap=SimpleNamespace(name='promod3_database',logical_work=20.)
            self.assertIsNone(failure_charge(cap,folder)['cpu_seconds'])
            (folder/'promod').mkdir()
            (folder/'promod/exit.json').write_text(json.dumps({'physical_cpu_seconds':4.5}))
            self.assertEqual(failure_charge(cap,folder)['logical_work'],4.5)

    def test_command_identity_binds_executable_and_script_bytes(self):
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            script=Path(tmp)/'worker.py';script.write_text('pass\n')
            first=command_identity([sys.executable,str(script)])
            script.write_text('print(1)\n')
            second=command_identity([sys.executable,str(script)])
            self.assertNotEqual(first,second)
            with self.assertRaises(ValueError): command_identity([])


if __name__=='__main__':unittest.main()
