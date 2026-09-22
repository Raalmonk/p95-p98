"""Explicit source-only observations for the continuous legacy NGK host.

Scoring takes place on clones. Neither the original input nor live working/MC
poses are scored or changed by this adapter. Targets and data identities are
not accepted by its constructor. The caller accounts for observation work.
"""
from __future__ import annotations

import math
from copy import deepcopy

from .source_decision_observation import observe_decision_state


CONTEXT_FIELDS = (
    'stage', 'site', 'phase', 'outer', 'inner', 'round', 'score_epoch', 'step',
    'counts', 'work', 'remaining_work', 'history', 'archive',
    'native_temperature', 'proposal_weights', 'acceptance_weights',
    'candidate_energy', 'current_energy', 'energy_delta', 'lowest_energy',
    'loop_start', 'loop_stop',
)
VIEW_FIELDS = CONTEXT_FIELDS + (
    'schema', 'sequence', 'loop_intervals_zero_based', 'coordinate_comparison',
    'working_state', 'accepted_current', 'working_minus_current', 'archive_displacements',
)
POSE_MUTATING_COUNTS = ('kic', 'repack', 'rotamer_trials', 'minimize', 'restore', 'mc_trials')


def backbone_export(pose):
    """Only sequence, canonical residue name and N/CA/C/O coordinates."""
    rows = []
    sequence = pose.sequence()
    for i in range(1, pose.size() + 1):
        residue = pose.residue(i)
        atoms = {}
        for name in ('N', 'CA', 'C', 'O'):
            if residue.has(name):
                xyz = residue.xyz(name)
                value = [float(xyz.x), float(xyz.y), float(xyz.z)]
                if not all(math.isfinite(x) for x in value):
                    raise ValueError('Nonfinite source coordinates')
                atoms[name] = value
        rows.append(dict(index=i, aa=sequence[i-1], name=residue.name3(), atoms=atoms))
    return dict(projection=dict(sequence=sequence), residues=rows)


def ca_distance_summary(a, b, residues):
    values = []
    for i in residues:
        left, right = a['residues'][i]['atoms'], b['residues'][i]['atoms']
        if 'CA' in left and 'CA' in right:
            values.append(math.dist(left['CA'], right['CA']))
    return dict(observed_count=len(values), missing_count=len(residues)-len(values),
                mean_A=math.fsum(values)/len(values) if values else None,
                maximum_A=max(values) if values else None)


def subtract_terms(left, right):
    # Terms missing in either observation are missing, never silently zero.
    return {name: left[name]-right[name] if name in left and name in right else None
            for name in sorted(set(left) | set(right))}


class SourceObservations:
    def __init__(self, source_pose, *, loops, polymer_edges, fixed_score):
        self.raw = backbone_export(source_pose)
        self.sequence = self.raw['projection']['sequence']
        self.loops = [list(x) for x in loops]
        self.edges = [list(x) for x in polymer_edges]
        self.fixed_score = fixed_score.clone()
        self.selected = sorted({i for start, end in self.loops for i in range(start, end+1)})
        self._cache = {}
        # Reuse the qualified pure geometry projector's bounds/connectivity
        # validation before any policy invocation. It computes no native score.
        observe_decision_state(self.raw, self.raw, sequence=self.sequence,
                               loops=self.loops, polymer_edges=self.edges)

    def scored(self, host, pose, score):
        clone = pose.clone()
        value = float(score(clone))
        residues = [float(clone.energies().residue_total_energy(i))
                    for i in range(1, clone.size()+1)]
        terms = {}
        for term in score.get_nonzero_weighted_scoretypes():
            name = host.r.core.scoring.name_from_score_type(term)
            terms[str(name)] = float(clone.energies().total_energies()[term] * score.get_weight(term))
        if not all(math.isfinite(x) for x in [value, *residues, *terms.values()]):
            raise ValueError('Nonfinite source-only energy observation')
        host.counts['observation_score_calls'] += 1
        return dict(total=value, weighted_terms=terms, weighted_residue_energy=residues,
                    per_residue_sum=math.fsum(residues))

    def state(self, host, pose, active):
        export = backbone_export(pose)
        energy = self.scored(host, pose, active)
        fixed = self.scored(host, pose, self.fixed_score)
        source = observe_decision_state(self.raw, export, sequence=self.sequence,
                                       loops=self.loops, polymer_edges=self.edges,
                                       per_residue_energy=energy['weighted_residue_energy'])
        per_loop = []
        for index, (start, end) in enumerate(self.loops):
            per_loop.append(dict(loop_index=index,
                active_energy=math.fsum(energy['weighted_residue_energy'][start:end+1]),
                fixed_energy=math.fsum(fixed['weighted_residue_energy'][start:end+1])))
        # The source projector already carries active per-residue values in the
        # selected neighborhood. Fixed values for the same residues are explicit.
        for residue in source['residues']:
            residue['fixed_weighted_residue_energy'] = fixed['weighted_residue_energy'][residue['index']]
        for record in (energy, fixed):
            del record['weighted_residue_energy']
        return dict(source=source, active=energy, fixed=fixed, loop_energies=per_loop), export

    def cached_state(self, role, host, pose, active):
        """Reuse only unchanged host states, never a near-duplicate conformation.

        Keys are host-owned native mutation/MC counters and the score epoch.
        The legacy host must count every listed operation before invoking it;
        recover_low occurs only at epoch boundaries. Cache reuse is storage/
        diagnostic engineering: every observation request remains a logically
        charged operation, and actual score calls/cache hits are separate.
        """
        if role == 'current':
            key = (host.score_epoch, host.counts['mc_accepts'], host.counts['restore'])
        elif role == 'working':
            key = (host.score_epoch, *(host.counts[name] for name in POSE_MUTATING_COUNTS))
        else:
            raise ValueError('Unknown observation state role')
        previous = self._cache.get(role)
        if previous is not None and previous[0] == key:
            host.counts['observation_cache_hits'] += 1
            return previous[1]
        result = self.state(host, pose, active)
        self._cache[role] = key, result
        return result

    def __call__(self, host, context):
        view = {name: deepcopy(context.get(name)) for name in CONTEXT_FIELDS}
        view['archive'] = [dict(slot=slot, **deepcopy(meta))
                           for slot, meta in sorted(host.archive_meta.items())]
        view.update(schema='source-legacy-ngk-observation-v1', sequence=self.sequence,
                    loop_intervals_zero_based=deepcopy(self.loops),
                    coordinate_comparison='unaligned_source_frame')
        # The acceptance score is common to both states, including the native
        # initial-repack epoch where proposal and acceptance weights differ.
        active = host.mc.score_function() if host.mc is not None else host.local_score
        working, export = self.cached_state('working', host, host.pose, active)
        view['working_state'] = working
        if host.mc is not None:
            accepted, accepted_export = self.cached_state('current', host, host.mc.last_accepted_pose(), active)
            view['accepted_current'] = accepted
            view['working_minus_current'] = dict(
                active_energy=working['active']['total']-accepted['active']['total'],
                fixed_energy=working['fixed']['total']-accepted['fixed']['total'],
                active_terms=subtract_terms(working['active']['weighted_terms'], accepted['active']['weighted_terms']),
                loop_ca_displacement=ca_distance_summary(export, accepted_export, self.selected))
        else:
            view['accepted_current'] = None
            view['working_minus_current'] = None
        view['archive_displacements'] = [dict(slot=slot,
            loop_ca_displacement=ca_distance_summary(export, backbone_export(pose), self.selected))
            for slot, pose in sorted(host.archive.items())]
        return view
