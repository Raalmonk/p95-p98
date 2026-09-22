"""Synthetic all-atom identity fixtures; no native load or score."""
from copy import deepcopy
import json
import unittest
from p95p98.native import source_connection_geometry as geometry
from p95p98.native.histidine_geometry import validation_view, correct_histidine_observation


def fixture():
    names = ['N','CA','C','O','ND1','NE2','HE2']
    elements = dict(zip(names,['N','C','C','O','N','N','H']))
    atoms = dict(zip(names,[[0.,0.,0.],[1.458,0.,0.],[2.983,0.,0.],[4.2,0.,0.],
                          [0.,2.,0.],[1.,2.,0.],[2.,2.,0.]]))
    source = dict(projection=dict(sequence='H',fold_tree='fixture',topology=[['HIS',names]]),
        residues=[dict(index=1,name='HIS',chain='A',atoms=atoms,elements=elements,
                       atomic_numbers={k:{'N':7,'C':6,'O':8,'H':1}[v] for k,v in elements.items()})])
    source['projection']['coordinates_sha256']=geometry._coordinate_hash(source)
    contract = dict(profile=geometry.PROFILE,gap_exemptions_enabled=False,
        source_projection=deepcopy(source['projection']),bindings=[dict(chain='A')],
        source_residue_names=['HIS'],removed_peptide_boundaries=[],preexisting_unresolved_connections=[])
    contract['contract_sha256']=geometry.identity(contract)
    current = deepcopy(source)
    current['projection']['topology'][0]=['HIS_D',names[:-1]+['HD1']]
    for key in ('atoms','elements','atomic_numbers'):
        current['residues'][0][key]['HD1']=current['residues'][0][key].pop('HE2')
    current['residues'][0]['atoms']['HD1']=[0.,3.,0.]
    current['projection']['coordinates_sha256']=geometry._coordinate_hash(current)
    obs=dict(expected_peptide_bonds=[],extreme_contacts=[],backbone_bond_rms_error_A=0.,
        custom_short_contact_score=0.,valid=True,local_energy=-123.456,global_energy=-123.456,
        sequence_exact=True,required_heavy_complete=True,finite_coordinates=True)
    return source,current,contract,obs


class HistidineTests(unittest.TestCase):
    def test_tautomer_view_preserves_real_coords_energy_and_original_contract(self):
        source,current,contract,obs=fixture()
        before=json.dumps([source,current,contract,obs],sort_keys=True)
        corrected=correct_histidine_observation(current,obs,contract,source,geometry=geometry)
        self.assertEqual(before,json.dumps([source,current,contract,obs],sort_keys=True))
        self.assertEqual(corrected['local_energy'],obs['local_energy'])
        self.assertEqual(corrected['extreme_contacts'],obs['extreme_contacts'])
        evidence=corrected['source_connection_geometry']
        self.assertEqual(evidence['contract_sha256'],contract['contract_sha256'])
        self.assertNotEqual(evidence['derived_validation_view_sha256'],contract['contract_sha256'])
        self.assertEqual(evidence['histidine_tautomer_adaptations'][0]['endpoint_hydrogen'],'HD1')

    def test_reverse_and_unchanged(self):
        source,current,contract,obs=fixture()
        reverse=deepcopy(contract);reverse['source_projection']=deepcopy(current['projection'])
        reverse['contract_sha256']=geometry.identity({k:v for k,v in reverse.items() if k!='contract_sha256'})
        _,changes=validation_view(source,reverse,current,geometry=geometry)
        self.assertEqual(changes[0]['endpoint_hydrogen'],'HE2')
        view,changes=validation_view(source,contract,source,geometry=geometry)
        self.assertEqual(view,contract);self.assertEqual(changes,[])

    def test_non_his_and_patch_changes_still_rejected(self):
        for name in ('HIP','HIS_D:disulfide','HIS_D:NtermProteinFull','CYS:disulfide','DHIS_D'):
            source,current,contract,obs=fixture()
            current['projection']['topology'][0][0]=name
            with self.assertRaises(ValueError):validation_view(current,contract,source,geometry=geometry)

    def test_missing_extra_or_nonhydrogen_rejected(self):
        for mode in ('missing','extra','carbon','heavy'):
            source,current,contract,obs=fixture()
            if mode=='missing':current['projection']['topology'][0][1].remove('HD1')
            elif mode=='extra':current['projection']['topology'][0][1].append('HE2')
            elif mode=='carbon':current['residues'][0]['elements']['HD1']='C'
            else:current['projection']['topology'][0][1][0]='NX'
            with self.assertRaises(ValueError):validation_view(current,contract,source,geometry=geometry)

    def test_original_identity_checks_not_bypassed(self):
        for mode in ('coordinate','chain','sequence','foldtree','contract'):
            source,current,contract,obs=fixture()
            if mode=='coordinate':current['residues'][0]['atoms']['CA'][0]+=1.
            elif mode=='chain':current['residues'][0]['chain']='B'
            elif mode=='sequence':current['projection']['sequence']='A'
            elif mode=='foldtree':current['projection']['fold_tree']='changed'
            else:contract['contract_sha256']='wrong'
            with self.assertRaises(ValueError):validation_view(current,contract,source,geometry=geometry)


if __name__=='__main__':unittest.main()
