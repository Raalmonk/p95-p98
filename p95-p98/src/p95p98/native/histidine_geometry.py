"""MC-only neutral L-histidine identity adapter; no coordinate/energy edits."""
from copy import deepcopy


def validation_view(export, contract, source_export, *, geometry):
    """Return an ephemeral validation contract and explicit admitted changes.

    The original source contract stays immutable. A view changes only the
    residue topology descriptions for exact HIS/HIS_D neutral tautomer pairs.
    Current atom indices remain current atom indices, including contact records.
    """
    geometry._validate(source_export, contract)
    if source_export['projection'] != contract['source_projection']:
        raise ValueError('Histidine adapter requires the exact original RAW source')
    source = contract['source_projection']
    current = export['projection']
    if len(export['residues']) != len(source_export['residues']):
        raise ValueError('Candidate residue count differs')
    for key in ('sequence', 'fold_tree'):
        if current[key] != source[key]:
            raise ValueError('Candidate '+key+' differs from frozen source')
    if len(current['topology']) != len(source['topology']):
        raise ValueError('Candidate topology differs from frozen source')
    changes = []
    for i, (before, after) in enumerate(zip(source['topology'], current['topology'])):
        if before == after:
            continue
        old_type, new_type = before[0].split(':'), after[0].split(':')
        if (set((old_type[0],new_type[0])) != {'HIS','HIS_D'} or
                old_type[1:] != new_type[1:] or source['sequence'][i] != 'H'):
            raise ValueError('Candidate topology differs from frozen source')
        old_h = 'HE2' if old_type[0] == 'HIS' else 'HD1'
        new_h = 'HE2' if new_type[0] == 'HIS' else 'HD1'
        old_names = [a.strip() for a in before[1]]
        new_names = [a.strip() for a in after[1]]
        if (len(set(old_names)) != len(old_names) or len(set(new_names)) != len(new_names) or
                set(old_names)-set(new_names) != {old_h} or
                set(new_names)-set(old_names) != {new_h} or
                new_h in old_names or old_h in new_names):
            raise ValueError('Candidate topology differs from frozen source')
        prior, row = source_export['residues'][i], export['residues'][i]
        if set(prior['atoms']) != set(old_names) or set(row['atoms']) != set(new_names):
            raise ValueError('Candidate atom/chain mapping differs')
        for record, hydrogen in ((prior,old_h),(row,new_h)):
            if record['elements'].get(hydrogen) != 'H' or record['atomic_numbers'].get(hydrogen) != 1:
                raise ValueError('Tautomer exchanged atom must be hydrogen')
        common = set(old_names)&set(new_names)
        if any(prior['elements'].get(a) != row['elements'].get(a) or
               prior['atomic_numbers'].get(a) != row['atomic_numbers'].get(a) for a in common):
            raise ValueError('Tautomer common atom elements differ')
        changes.append(dict(residue_index=i+1, source_type=before[0], endpoint_type=after[0],
                            source_hydrogen=old_h, endpoint_hydrogen=new_h))
    view = deepcopy(contract)
    if changes:
        view['source_projection']['topology'] = deepcopy(current['topology'])
        view['contract_sha256'] = geometry.identity({k:v for k,v in view.items() if k!='contract_sha256'})
    # Reuses every original check: identity hashes, sequence, full atom sets,
    # consecutive indices, count, chain, name3, fold tree and finite Cartesian.
    geometry._validate(export, view)
    return view, changes


def correct_histidine_observation(export, observation, contract, source_export, *, geometry):
    view, changes = validation_view(export, contract, source_export, geometry=geometry)
    corrected = geometry.correct_exported_observation(export, observation, view)
    evidence = corrected['source_connection_geometry']
    evidence['contract_sha256'] = contract['contract_sha256']
    evidence['derived_validation_view_sha256'] = view['contract_sha256']
    evidence['histidine_tautomer_adaptations'] = changes
    evidence['endpoint_coordinates_and_energy_unchanged'] = True
    return corrected
