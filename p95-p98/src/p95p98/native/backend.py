"""Runtime class extracted from the evaluated host; no training runner."""
import hashlib
import math
import pickle
import struct
import sys

class RosettaBackend:
    def __init__(self, flags):
        if sys.platform != 'linux':
            raise RuntimeError('The pinned PyRosetta runtime requires Linux')
        import pyrosetta
        self.pyrosetta = pyrosetta
        pyrosetta.init(extra_options=flags)
        self.rosetta = pyrosetta.rosetta
        self.scorefxn = pyrosetta.create_score_function('ref2015')
        self.serialization_supported = None

    def rng(self):
        stream = self.rosetta.std.ostringstream()
        self.rosetta.numeric.random.rg().saveState(stream)
        return stream.str()

    def restore_rng(self, state):
        self.rosetta.numeric.random.rg().restoreState(self.rosetta.std.istringstream(state))

    def isolated_pose(self, pose):
        result = self.rosetta.core.pose.Pose()
        result.detached_copy(pose)
        return result

    def projection(self, pose):
        atoms, topology = [], []
        for r in range(1, pose.total_residue() + 1):
            residue = pose.residue(r)
            topology.append([residue.name(), [residue.atom_name(a) for a in range(1, residue.natoms() + 1)]])
            for a in range(1, residue.natoms() + 1):
                xyz = residue.xyz(a)
                atoms.append(struct.pack('!ddd', xyz.x, xyz.y, xyz.z))
        return dict(coordinates_sha256=hashlib.sha256(b''.join(atoms)).hexdigest(),
                    topology=topology, fold_tree=str(pose.fold_tree()), sequence=pose.sequence())

    def pack(self, pose):
        state = self.rng()
        try:
            if self.serialization_supported is not False:
                try:
                    raw = pickle.dumps(pose, protocol=5)
                    restored = pickle.loads(raw)
                    if self.projection(restored) != self.projection(pose):
                        raise RuntimeError('Native Pose serialization projection mismatch')
                    self.serialization_supported = True
                    return raw, True
                except Exception:
                    if self.serialization_supported is True:
                        raise
                    self.serialization_supported = False
            atoms = [(r, a, tuple(float(v) for v in (pose.residue(r).xyz(a).x,
                      pose.residue(r).xyz(a).y, pose.residue(r).xyz(a).z)))
                     for r in range(1, pose.total_residue() + 1)
                     for a in range(1, pose.residue(r).natoms() + 1)]
            return pickle.dumps(dict(atoms=atoms, projection=self.projection(pose)), protocol=5), False
        finally:
            self.restore_rng(state)

    def load(self, path):
        return self.pyrosetta.pose_from_file(str(path))

    def apply(self, pose, xml, kind):
        objects = self.rosetta.protocols.rosetta_scripts.XmlObjects.create_from_string(xml)
        import xml.etree.ElementTree as ET
        name = ET.fromstring(xml).find('MOVERS')[0].get('name')
        mover = objects.get_mover(name)
        mover.apply(pose)
        success = mover.get_last_move_status() == self.rosetta.protocols.moves.MS_SUCCESS
        result = dict(apply_status=str(mover.get_last_move_status()), apply_success=success,
                      closure_success=None)
        if kind in ('rama', 'perturb'):
            result['closure_success'] = bool(mover.last_run_successful())
            result['apply_success'] = success and result['closure_success']
        return result

    def score(self, pose):
        state = self.rng()
        clone = pose.clone()
        try:
            total = float(self.scorefxn(clone))
            scoring = self.rosetta.core.scoring
            names = ['fa_rep', 'fa_atr', 'cart_bonded', 'rama_prepro', 'omega', 'p_aa_pp',
                     'hbond_sr_bb', 'hbond_lr_bb', 'hbond_bb_sc', 'hbond_sc']
            energies, weights = clone.energies().total_energies(), self.scorefxn.weights()
            terms = {name: float(energies[getattr(scoring, name)] * weights[getattr(scoring, name)])
                     for name in names}
            return dict(score_function='ref2015', total=total, weighted_components=terms)
        finally:
            self.restore_rng(state)

    def integrated_observation(self, pose, *, local_indices, expected_sequence):
        """Full precision source-only observations; no violation reduction.

        Atom topology comes from residue types plus fixed expected peptide bonds,
        never from inferred distances. All per-bond and extreme-contact deficits
        are retained; the pending within-condition score convention is not used.
        """
        import numpy as np
        from .pdb_metrics import Residue, backbone_bond_rms_error, clashscore
        before = self.rng()
        clone = self.isolated_pose(pose)
        scorefxn = self.scorefxn.clone()
        options = scorefxn.energy_method_options()
        options.hbond_options().decompose_bb_hb_into_pair_energies(True)
        scorefxn.set_energy_method_options(options)
        try:
            total = float(scorefxn(clone))
            per_residue = [float(clone.energies().residue_total_energy(i))
                           for i in range(1, clone.total_residue()+1)]
            residues, coordinates, atom_ids, adjacency = [], [], [], {}
            required_complete = True
            for i in range(1, clone.total_residue()+1):
                res = clone.residue(i)
                parsed = Residue(res.name3(), 'A', i, '')
                for a in range(1, res.natoms()+1):
                    if res.atom_type(a).is_hydrogen() or res.atom_type(a).is_virtual():
                        continue
                    key = (i, a)
                    xyz = res.xyz(a)
                    point = np.array([xyz.x, xyz.y, xyz.z])
                    coordinates.append(point); atom_ids.append(key)
                    parsed.atoms[res.atom_name(a).strip()] = point
                    parsed.elements[res.atom_name(a).strip()] = res.atom_type(a).element()
                    adjacency[key] = {(i, int(b)) for b in res.bonded_neighbor(a)
                                      if not res.atom_type(b).is_hydrogen()
                                      and not res.atom_type(b).is_virtual()}
                required_complete &= {'N', 'CA', 'C', 'O'} <= set(parsed.atoms)
                residues.append(parsed)
            # Include known chemical inter-residue connections (e.g. disulfide).
            for i in range(1, clone.total_residue()+1):
                res = clone.residue(i)
                for connection in range(1, res.n_possible_residue_connections()+1):
                    other = res.connected_residue_at_resconn(connection)
                    if not other:
                        continue
                    partner_connection = res.residue_connection_conn_id(connection)
                    a = res.type().residue_connection(connection).atomno()
                    b = clone.residue(other).type().residue_connection(partner_connection).atomno()
                    if (i,a) in adjacency and (other,b) in adjacency:
                        adjacency[(i,a)].add((other,b)); adjacency[(other,b)].add((i,a))
            cn = []
            for i in range(1, clone.total_residue()):
                first, second = clone.residue(i), clone.residue(i+1)
                if not first.has('C') or not second.has('N'):
                    required_complete = False
                    cn.append({'residues': [i,i+1], 'distance_A': None})
                    continue
                a,b = (i,first.atom_index('C')),(i+1,second.atom_index('N'))
                adjacency[a].add(b); adjacency[b].add(a)
                distance = float(np.linalg.norm(residues[i-1].atoms['C']-residues[i].atoms['N']))
                cn.append({'residues': [i,i+1], 'distance_A': distance,
                           'outside_A': max(1.0-distance, distance-1.7, 0.0)})
            xyz = np.asarray(coordinates)
            finite = bool(np.isfinite(xyz).all())
            extreme = []
            for a,key in enumerate(atom_ids):
                excluded = set(adjacency[key]) | {key}
                for neighbor in adjacency[key]:
                    excluded.update(adjacency[neighbor])
                for offset in np.flatnonzero(np.linalg.norm(xyz[a+1:]-xyz[a],axis=1)<0.5):
                    b = a+1+int(offset)
                    if atom_ids[b] not in excluded:
                        distance = float(np.linalg.norm(xyz[a]-xyz[b]))
                        extreme.append({'atoms': [key,atom_ids[b]], 'distance_A': distance,
                                        'deficit_A': 0.5-distance})
            bond = float(backbone_bond_rms_error(residues))
            contact = float(clashscore(residues))
            valid = (pose.sequence()==expected_sequence and required_complete and finite
                     and all(x.get('outside_A')==0 for x in cn)
                     and bond<=0.05 and contact<=30 and not extreme)
            observation = {'global_energy':total,
                    'local_energy':sum(per_residue[i] for i in local_indices),
                    'per_residue_energy':per_residue,
                    'energy_residual':total-sum(per_residue),
                    'observer_score_function':'ref2015_bb_hbond_pair_decomposition',
                    'sequence_exact':pose.sequence()==expected_sequence,
                    'required_heavy_complete':bool(required_complete),
                    'finite_coordinates':finite,'expected_peptide_bonds':cn,
                    'backbone_bond_rms_error_A':bond,'custom_short_contact_score':contact,
                    'extreme_contacts':extreme,'valid':bool(valid),
                    'violation_reduction_status':'MAXIMUM_STANDARDIZED_POSITIVE_EXCEEDANCE'}
            from .numerics import geometry_feedback
            observation['geometry_feedback'] = geometry_feedback(observation)
            return observation
        finally:
            self.restore_rng(before)
