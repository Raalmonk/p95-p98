"""Load explicit frozen work tariffs without native imports or calibration."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

OPERATION_PRICES = frozenset(('kic', 'repack', 'rotamer_trials', 'minimize',
                              'observe_state', 'controller', 'archive_save', 'restore'))
TARIFF_FIELDS = frozenset(('view', 'fresh_state', 'cached_state', 'archive_displacement'))


def positive(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and positive')
    return value


def validate_work_profile(profile):
    if not isinstance(profile, dict) or profile.get('schema') != 'p95p98-work-profile-v1':
        raise ValueError('Expected p95p98-work-profile-v1')
    if not isinstance(profile.get('name'), str) or not profile['name']:
        raise ValueError('Work profile name is required')
    for field, required in [('operation_prices', OPERATION_PRICES), ('tariff', TARIFF_FIELDS)]:
        values = profile.get(field)
        if not isinstance(values, dict) or not required <= values.keys():
            raise ValueError(f'{field} requires {sorted(required)}')
        for key in required:
            positive(values[key], f'{field}.{key}')
    if profile['tariff'].get('status') != 'MEASURED':
        raise ValueError('Tariff must retain measured provenance')
    positive(profile.get('policy_setup_work'), 'policy_setup_work')
    positive(profile.get('delivery_reserve_cpu_seconds'), 'delivery_reserve_cpu_seconds')
    provenance = profile.get('provenance_sha256')
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError('Provenance hashes are required')
    for value in provenance.values():
        if not isinstance(value, str) or len(value) != 64 or set(value) - set('0123456789abcdef'):
            raise ValueError('Invalid provenance SHA256')
    return deepcopy(profile)


def load_work_profile(path):
    """An explicit path is required; there is deliberately no default profile."""
    if path is None:
        raise ValueError('An explicit --work-profile path is required')
    raw = Path(path).read_bytes()
    profile = validate_work_profile(json.loads(raw))
    profile['profile_sha256'] = hashlib.sha256(raw).hexdigest()
    return profile


def reserve_observation(tariff):
    for name in TARIFF_FIELDS:
        positive(tariff.get(name), 'tariff.' + name)
    return (tariff['view'] + 2 * max(tariff['fresh_state'], tariff['cached_state'])
            + 8 * tariff['archive_displacement'])


def native_prices(profile):
    profile = validate_work_profile(profile)
    result = dict(profile['operation_prices'])
    result['observe_state'] = reserve_observation(profile['tariff'])
    return result
