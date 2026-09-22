"""Portable source-only adapter around the evaluated native methods."""
import copy
import hashlib
import time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
from ..controller import State, PreparationPending, digest, public_features

def bytes_sha(value):
    return hashlib.sha256(value).hexdigest()

class NativeSource:
    def __init__(self, pdb_path, loops, sequence, seed, input_kind='W', *, local_energy_residues):
        from .backend import RosettaBackend
        from .fingerprint import fingerprint
        from .export import export_source_pose
        from .observations import SourceObservations
        from .source_connection_geometry import build_connection_contract
        from .legacy_refine import ROSETTA_VERSION
        if input_kind not in ('W', 'S', 'hard'):
            raise ValueError('input_kind must be W, S, or hard')
        if type(seed) is not int or not 1 <= seed <= 2147483647:
            raise ValueError('seed must be an integer in 1..2147483647')
        definitions = []
        occupied = set()
        for item in loops:
            start, stop, cut = (item[k] for k in ('start', 'stop', 'cut'))
            if (any(type(x) is not int for x in (start,stop,cut)) or
                    not 1 < start <= cut < stop < len(sequence) or stop-start+1 < 3):
                raise ValueError('Loops require internal 1-based intervals of at least three residues')
            if 'extended' in item and type(item['extended']) is not bool:
                raise ValueError('extended must be boolean')
            members = set(range(start,stop+1))
            if occupied & members or item.get('skip',0.) != 0.:
                raise ValueError('Overlapping or skipped loops are unsupported')
            occupied |= members
            definitions.append(dict(start=start,stop=stop,cut=cut,skip=0.,extended=item.get('extended',False)))
        if not definitions:
            raise ValueError('At least one loop is required')
        if (not isinstance(local_energy_residues,list) or not local_energy_residues
                or any(type(i) is not int or not 1 <= i <= len(sequence) for i in local_energy_residues)
                or len(set(local_energy_residues)) != len(local_energy_residues)
                or not occupied <= set(local_energy_residues)):
            raise ValueError('local_energy_residues must explicitly identify unique 1-based target residues including all loops')
        raw = Path(pdb_path).read_bytes()
        flags = ('-ex1 -ex2 -ex2aro -mute all -ignore_zero_occupancy false '
                 '-ignore_unrecognized_res -constant_seed -jran '+str(seed)+
                 ' -unmute protocols.generalized_kinematic_closure.GeneralizedKIC')
        self.backend = RosettaBackend(flags)
        self.pyrosetta, self.r = self.backend.pyrosetta, self.backend.rosetta
        if str(self.r.utility.Version.version()) != ROSETTA_VERSION:
            raise ValueError('Pinned PyRosetta runtime version required: '+ROSETTA_VERSION)
        self.r.numeric.random.rg().set_seed('mt19937', seed)
        self.pose = self.backend.load(pdb_path)
        if self.pose.sequence() != sequence:
            raise ValueError('Loaded prepared PDB sequence does not match target sequence')
        if any(not self.pose.residue(i).is_protein() for i in range(1,self.pose.size()+1)):
            raise ValueError('Only protein residues are supported')
        options = self.backend.scorefxn.energy_method_options()
        options.hbond_options().decompose_bb_hb_into_pair_energies(True)
        self.backend.scorefxn.set_energy_method_options(options)
        self.fingerprint = fingerprint
        self.definitions = definitions
        self.loops0 = [[x['start']-1,x['stop']-1] for x in definitions]
        self.loop_lengths = [b-a+1 for a,b in self.loops0]
        self.input_kind = input_kind
        self.original_export = export_source_pose(self.pose,backend=self.backend)
        sha = bytes_sha(raw)
        self.geometry = build_connection_contract(source_pdb=raw,original_source_pdb=raw,
            source_sha256=sha,original_source_sha256=sha,source_export=self.original_export,
            bindings=self.original_export['source_bindings'],movable_loop=sorted(occupied))
        boundaries = {tuple(x['residues']) for x in self.geometry['removed_peptide_boundaries']}
        edges = [[i-1,i] for i in range(1,self.pose.size()) if (i,i+1) not in boundaries]
        self.context = dict(loops0=[list(range(a,b+1)) for a,b in self.loops0],
                            polymer_edges=edges,source_sha256=sha)
        self.binding = dict(local_energy_residues0=sorted(i-1 for i in local_energy_residues),
                            global_energy_residues0=list(range(self.pose.size())))
        self.observer = SourceObservations(self.pose,loops=self.loops0,
            polymer_edges=edges,fixed_score=self.backend.scorefxn)
        self.observation_cache, self.observation_costs = {}, []
        self.context_sha = digest(dict(runtime=str(self.r.utility.Version.version()),
            loops=definitions,source_context=self.context,energy_regions=self.binding,
            initializer=dict(init_flags=flags)))
        self.raw = self.state(self.pose)

    def compatible(self, pose):
        """Check exact chemistry/FoldTree, allowing only existing neutral HIS adapter.

        Returns explicit histidine adaptations; raises ValueError on incompatibility.
        Does not score, modify coordinates, or consult reference structures.
        """
        from .export import export_source_pose
        from .histidine_geometry import validation_view
        from . import source_connection_geometry
        exported = export_source_pose(pose, backend=self.backend)
        _, changes = validation_view(exported,self.geometry,self.original_export,
                                     geometry=source_connection_geometry)
        before, after = self.fingerprint(self.pose), self.fingerprint(pose)
        if before['constraints'] != after['constraints']:
            raise ValueError('Candidate constraints differ from source')
        for original, candidate in zip(before['residues'],after['residues']):
            if (original['connections'] != candidate['connections'] or
                    original['variants'] != candidate['variants']):
                raise ValueError('Candidate chemical connections or variants differ from source')
        return changes

    def rng(self):
        s = self.r.std.ostringstream()
        self.r.numeric.random.rg().saveState(s)
        return s.str()

    def set_rng(self, state):
        self.backend.restore_rng(state)

    def fingerprint_binding(self, pose):
        fp = self.fingerprint(pose)
        topology = dict(sequence=fp['sequence'], fold_tree=fp['fold_tree'],
            constraints=fp['constraints'], residues=[{k:r[k] for k in
                ('name','chain','connections','variants')} for r in fp['residues']])
        return dict(state_sha256=digest(fp), context_sha256=self.context_sha,
                    topology_sha256=digest(topology), sequence_sha256=bytes_sha(pose.sequence().encode()),
                    loops_sha256=digest(self.definitions), rng_sha256=bytes_sha(self.rng().encode()))

    def export(self, pose):
        from .export import export_endpoint
        return export_endpoint(pose, self.binding, backend=self.backend, geometry_contract=self.geometry)

    def features(self, pose, binding):
        start = time.process_time()
        key = (binding['state_sha256'], self.context_sha)
        hit = key in self.observation_cache
        if not hit:
            from .histidine_geometry import correct_histidine_observation
            from . import source_connection_geometry
            from .numerics import geometry_feedback
            before = self.rng()
            exported = self.export(pose)
            try:
                corrected = correct_histidine_observation(exported, exported['observation'],
                    self.geometry, self.original_export, geometry=source_connection_geometry)
                geo = geometry_feedback(corrected)
            except ValueError as exc:
                if 'topology' not in str(exc).lower():
                    raise
                geo = dict(disposition='UNINTERPRETABLE', condition_exceedances=None)
            dummy = SimpleNamespace(r=self.r, counts=Counter())
            detailed, _ = self.observer.state(dummy, pose, self.backend.scorefxn)
            local = []
            for residue in detailed['source']['residues']:
                torsion = residue['torsions_degrees']
                local.append(dict(index=residue['index'], aa=residue['aa'],
                    phi=torsion['phi']['value'], psi=torsion['psi']['value'], omega=torsion['omega']['value'],
                    contact_count=residue['nonlocal_ca_contacts']['count'],
                    fixed_energy=residue['fixed_weighted_residue_energy'],
                    source_displacement_A=residue['ca_displacement_A']['value'],
                    missing=residue['backbone_missing_count'] > 0))
            per_loop = []
            for i, item in enumerate(detailed['source']['loops']):
                per_loop.append(dict(loop_index=i, length=self.loop_lengths[i],
                    fixed_energy=detailed['loop_energies'][i]['fixed_energy'],
                    source_displacement_A=item['ca_displacement_mean_A']['value'],
                    contact_count=item['outside_loop_ca_contacts']['count']))
            ex = geo.get('condition_exceedances') or {}
            public = dict(sequence=pose.sequence(), input_kind=self.input_kind,
                loop_intervals=self.loops0, loop_lengths=self.loop_lengths,
                fixed_local_energy=exported['observation']['local_energy'],
                fixed_global_energy=exported['observation']['global_energy'],
                geometry_valid=geo['disposition']=='VALID',
                cn_exceedance=ex.get('cn'), bond_exceedance=ex.get('bond'),
                contact_exceedance=ex.get('contact'), extreme_exceedance=ex.get('extreme'),
                atom_count=sum(pose.residue(i).natoms() for i in range(1,pose.size()+1)),
                per_residue=local, per_loop=per_loop)
            if before != self.rng():
                raise PreparationPending('Source observations consumed native random numbers')
            self.observation_cache[key] = public_features(public), exported
        values = copy.deepcopy(self.observation_cache[key])
        self.observation_costs.append(dict(cache_hit=hit, cpu_seconds=time.process_time()-start))
        return values

    def state(self, pose):
        clone = pose.clone()
        binding = self.fingerprint_binding(clone)
        features, exported = self.features(clone, binding)
        return State(binding, features, dict(pose=clone, exported=exported, rng=self.rng())).validate()

    def clone_state(self, state):
        return State(copy.deepcopy(state.binding), copy.deepcopy(state.features),
            dict(pose=state.payload['pose'].clone(), exported=copy.deepcopy(state.payload['exported']),
                 rng=state.payload['rng']))

    def serialize_endpoint(self, state):
        """Source-only full-precision export for independent offline evaluation."""
        stream = self.r.std.ostringstream()
        self.r.core.io.pdb.dump_pdb(state.payload['pose'], stream)
        return dict(endpoint=state.payload['exported'], geometry_contract=self.geometry,
            pdb_text=stream.str(), state_binding=state.binding,
            source_context=self.context, target_available_to_policy=False)
