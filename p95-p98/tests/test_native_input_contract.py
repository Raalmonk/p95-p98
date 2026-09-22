"""Input boundary checks execute before importing or initializing PyRosetta."""
import unittest
from p95p98.native.runtime import NativeSource


class InputContract(unittest.TestCase):
    def arguments(self):
        return dict(pdb_path='not-read.pdb',loops=[dict(start=2,stop=4,cut=3)],
                    sequence='AAAAAA',seed=17,local_energy_residues=[1,2,3,4,5])

    def test_empty_local_region_rejected_before_native(self):
        args=self.arguments();args['local_energy_residues']=[]
        with self.assertRaisesRegex(ValueError,'local_energy_residues'):
            NativeSource(**args)

    def test_invalid_or_duplicate_energy_region_rejected(self):
        for residues in ([0,2],[2,2],[7],[True],[1,2],(1,2,3,4)):
            args=self.arguments();args['local_energy_residues']=residues
            with self.assertRaisesRegex(ValueError,'local_energy_residues'):
                NativeSource(**args)

    def test_terminal_or_short_loops_rejected(self):
        for loop in (dict(start=1,stop=4,cut=3),dict(start=2,stop=3,cut=2),
                     dict(start=2,stop=6,cut=3),dict(start=2,stop=4,cut=5),
                     dict(start=2,stop=4,cut=4)):
            args=self.arguments();args['loops']=[loop]
            with self.assertRaisesRegex(ValueError,'internal 1-based'):
                NativeSource(**args)

    def test_extended_type_is_not_coerced(self):
        for value in ('false',0,1,None):
            args=self.arguments();args['loops'][0]['extended']=value
            with self.assertRaisesRegex(ValueError,'extended must be boolean'):
                NativeSource(**args)

    def test_overlapping_loops_rejected(self):
        args=self.arguments();args['loops']*=2
        with self.assertRaisesRegex(ValueError,'Overlapping'):
            NativeSource(**args)

    def test_unsupported_kind_and_seed_rejected(self):
        for key,value in [('input_kind','unknown'),('seed',0),('seed',True)]:
            args=self.arguments();args[key]=value
            with self.assertRaises(ValueError):
                NativeSource(**args)


if __name__ == '__main__':
    unittest.main()
