"""Frozen source geometry reduction."""
import math

def geometry_feedback(observation):
    """Reduce each of the four fixed geometry conditions by its maximum."""
    if not all(observation.get(k) is True for k in
               ('sequence_exact', 'required_heavy_complete', 'finite_coordinates')):
        return {'disposition': 'UNINTERPRETABLE', 'invalid_score': -1.0}
    try:
        cn = [float(r['distance_A']) for r in observation['expected_peptide_bonds']]
        extreme = [float(r['distance_A']) for r in observation['extreme_contacts']]
        bond = float(observation['backbone_bond_rms_error_A'])
        contact = float(observation['custom_short_contact_score'])
        if not all(math.isfinite(x) for x in cn + extreme + [bond, contact]):
            raise ValueError('nonfinite geometry')
        if min(cn + extreme + [bond, contact], default=0) < 0:
            raise ValueError('negative geometric quantity')
    except (KeyError, TypeError, ValueError, OverflowError):
        return {'disposition': 'UNINTERPRETABLE', 'invalid_score': -1.0}
    values = [max((max(1.0-d, d-1.7, 0.0)/0.1 for d in cn), default=0.0),
              max(0.0, (bond-0.05)/0.05), max(0.0, (contact-30.0)/30.0),
              max((max(0.0, 0.5-d)/0.1 for d in extreme), default=0.0)]
    violation = max(values) + 0.1 * math.fsum(values)/4
    valid = violation == 0
    if observation.get('valid') is not valid:
        raise ValueError('retained geometry validity disagrees with approved reduction')
    return {'disposition': 'VALID' if valid else 'GEOMETRY_INVALID',
            'condition_exceedances': dict(zip(('cn', 'bond', 'contact', 'extreme'), values)),
            'violation': violation,
            'invalid_score': None if valid else -violation/(1+violation)}

