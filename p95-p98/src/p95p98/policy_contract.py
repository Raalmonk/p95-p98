"""Host-owned MC decision contract; no native calls, scoring or file access.

Capabilities come from the qualified legacy backend, not from candidate code.
The policy returns decisions; only the host updates poses, clocks and RNG.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math

SCHEMA = 'legacy-ngk-mc-control-v1'
ARCHIVE_SLOTS = 8
MEMORY_BYTES = 16384
EVENTS = ('pre_proposal', 'accept', 'retain', 'deliver')


class PolicyContractError(ValueError):
    pass


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _memory(value):
    if type(value) is not dict:
        raise PolicyContractError('memory must be a JSON object')
    try:
        payload = json.dumps(value, allow_nan=False, separators=(',', ':'))
    except (ValueError, TypeError, RecursionError) as exc:
        raise PolicyContractError('memory must contain finite JSON values') from exc
    if len(payload.encode()) > MEMORY_BYTES:
        raise PolicyContractError('memory exceeds fixed byte bound')
    return deepcopy(value)


def _slot(value, *, nullable=False):
    if nullable and value is None:
        return None
    if type(value) is not int or not 0 <= value < ARCHIVE_SLOTS:
        raise PolicyContractError('archive slot outside host range')
    return value


def native_decision(event, memory=None):
    """Pure default. Must consume no RNG or silently choose a candidate."""
    if event not in EVENTS:
        raise PolicyContractError('unknown decision event')
    choices = {
        'pre_proposal': dict(stop=False, restore_slot=None, loop_index=None,
                             perturbation='native', repack='native', minimize='native'),
        'accept': dict(mode='native', probability=None, temperature_multiplier=None),
        'retain': dict(save_slot=None, state='current'),
        'deliver': dict(state='native_low', slot=None),
    }
    return {'event': event, 'decision': choices[event], 'memory': _memory(memory or {})}


def validate_decision(answer, *, event, capabilities, populated_slots):
    """Validate only; applying an accepted decision is a separate host action.

    capabilities exact keys: loop_count, perturbations, repack, minimize,
    direct_probability, temperature, archive, stop. Tokens include only modes
    actually qualified on this input/phase. Failed proposals cannot be supplied
    as selectable archive states by the backend.
    """
    if event not in EVENTS or type(answer) is not dict:
        raise PolicyContractError('invalid event or decision envelope')
    if set(answer) != {'event', 'decision', 'memory'} or answer['event'] != event:
        raise PolicyContractError('decision envelope differs from requested event')
    if set(capabilities) != {'loop_count', 'perturbations', 'repack', 'minimize',
                             'direct_probability', 'temperature', 'archive', 'stop'}:
        raise PolicyContractError('unbound backend capability schema')
    if type(capabilities['loop_count']) is not int or capabilities['loop_count'] not in (1, 2):
        raise PolicyContractError('unqualified loop count')
    for name in ('direct_probability', 'temperature', 'archive', 'stop'):
        if type(capabilities[name]) is not bool:
            raise PolicyContractError('capability must be boolean')
    for name in ('perturbations', 'repack', 'minimize'):
        if type(capabilities[name]) not in (list, tuple) or 'native' not in capabilities[name]:
            raise PolicyContractError('capability must preserve native option')
        if any(type(v) is not str for v in capabilities[name]):
            raise PolicyContractError('invalid capability token')
    slots = set(populated_slots)
    for value in slots:
        _slot(value)
    decision = answer['decision']
    if type(decision) is not dict or set(decision) != set(native_decision(event)['decision']):
        raise PolicyContractError('event decision keys differ')
    if event == 'pre_proposal':
        if type(decision['stop']) is not bool or (decision['stop'] and not capabilities['stop']):
            raise PolicyContractError('stop is unavailable')
        restore = _slot(decision['restore_slot'], nullable=True)
        if restore is not None and (not capabilities['archive'] or restore not in slots):
            raise PolicyContractError('restore requires an existing allowed slot')
        loop = decision['loop_index']
        if loop is not None and (type(loop) is not int or not 0 <= loop < capabilities['loop_count']):
            raise PolicyContractError('loop index outside qualified input')
        for key, allowed in (('perturbation', 'perturbations'), ('repack', 'repack'), ('minimize', 'minimize')):
            if type(decision[key]) is not str or decision[key] not in capabilities[allowed]:
                raise PolicyContractError('operation not qualified: ' + key)
        if decision['stop'] and (restore is not None or loop is not None or
                                any(decision[k] != 'native' for k in ('perturbation', 'repack', 'minimize'))):
            raise PolicyContractError('stop must not also schedule or restore')
    elif event == 'accept':
        mode, probability, multiplier = (decision[k] for k in ('mode', 'probability', 'temperature_multiplier'))
        if mode == 'native':
            if probability is not None or multiplier is not None:
                raise PolicyContractError('native acceptance has no overrides')
        elif mode == 'probability':
            if (not capabilities['direct_probability'] or not _finite(probability) or
                    not 0 <= probability <= 1 or multiplier is not None):
                raise PolicyContractError('invalid direct acceptance probability')
        elif mode == 'temperature':
            if (not capabilities['temperature'] or not _finite(multiplier) or
                    not .5 <= multiplier <= 2 or probability is not None):
                raise PolicyContractError('invalid native temperature multiplier')
        else:
            raise PolicyContractError('unknown acceptance mode')
    elif event == 'retain':
        slot = _slot(decision['save_slot'], nullable=True)
        if slot is not None and not capabilities['archive']:
            raise PolicyContractError('archive not qualified')
        if decision['state'] not in ('current', 'candidate', 'native_low'):
            raise PolicyContractError('cannot save an unvisited state')
    else:
        if decision['state'] == 'archive':
            slot = _slot(decision['slot'])
            if not capabilities['archive'] or slot not in slots:
                raise PolicyContractError('delivery requires an existing archive state')
        elif decision['state'] not in ('current', 'native_low') or decision['slot'] is not None:
            raise PolicyContractError('delivery state differs')
    return dict(event=event, decision=deepcopy(decision), memory=_memory(answer['memory']))


def preserve_progress(before, after):
    """Required invariants for *policy* restore; fault resume is distinct."""
    for name in ('consumed_work', 'schedule_position', 'rng_state'):
        if before[name] != after[name]:
            raise PolicyContractError('policy restore rewound or changed ' + name)
    if before['score_epoch'] != after['score_epoch']:
        raise PolicyContractError('policy restore changed score epoch')
