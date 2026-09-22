"""Outer routing host: one mutable decide(view), immutable execution capabilities.

No Rosetta/ProMod3 import, file access, network access or automatic dispatcher.
Native functions must be injected with a reviewed, input-scoped qualification.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
import hashlib
import json
import math

ACTIONS = {'minimize', 'promod3_native', 'promod3_database', 'promod3_mc',
           'ngk_rebuild', 'ngk_refine', 'inspect'}
FEATURES = {'sequence', 'input_kind', 'loop_intervals', 'loop_lengths',
            'fixed_local_energy', 'fixed_global_energy', 'geometry_valid',
            'cn_exceedance', 'bond_exceedance', 'contact_exceedance',
            'extreme_exceedance', 'source_displacement_A', 'atom_count',
            'db_candidate_count', 'db_best_stem_rmsd_A', 'db_score_gap',
            'db_cluster_count', 'db_closed_fraction', 'per_loop', 'per_residue'}
LOCAL_FIELDS = {'index', 'loop_index', 'aa', 'phi', 'psi', 'omega',
                'cn_distance_A', 'contact_count', 'fixed_energy', 'active_energy',
                'source_displacement_A', 'missing', 'length'}
DIGEST_FIELDS = {'state_sha256', 'context_sha256', 'topology_sha256',
                 'sequence_sha256', 'loops_sha256', 'rng_sha256'}

class InvalidDecision(ValueError):
    pass

class PreparationPending(RuntimeError):
    """Missing execution evidence, not a biological failure fitness."""


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      allow_nan=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def checked_hash(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise PreparationPending('Expected an exact SHA256 binding')
    return value


def public_features(value):
    """Validate every nested value before exposing source-only features."""
    if type(value) is not dict or set(value) - FEATURES:
        raise PreparationPending('Unqualified or target-bearing feature field')
    counts = {'atom_count', 'db_candidate_count', 'db_cluster_count'}
    local_counts = {'index', 'loop_index', 'contact_count', 'length'}
    amino_acids = set('ACDEFGHIKLMNPQRSTVWYBXZJUO')
    def number(item, integer=False):
        if item is not None and (not finite(item) or
                (integer and (type(item) is not int or item < 0))):
            raise PreparationPending('Feature requires a finite scalar of the declared type')
    def integers(item, interval=False):
        if type(item) is not list or len(item) > 100000:
            raise PreparationPending('Bounded integer-list feature required')
        if interval:
            for pair in item:
                if (type(pair) is not list or len(pair) != 2 or
                        any(type(x) is not int or x < 0 for x in pair) or pair[0] > pair[1]):
                    raise PreparationPending('Invalid loop interval')
        elif any(type(x) is not int or x <= 0 for x in item):
            raise PreparationPending('Loop lengths must be positive integers')
    result = {key: None for key in sorted(FEATURES)}
    for key, item in value.items():
        if item is None:
            continue
        if key in ('per_loop', 'per_residue'):
            if type(item) is not list or len(item) > 100000:
                raise PreparationPending('Bounded local feature list required')
            for row in item:
                if type(row) is not dict or set(row) - LOCAL_FIELDS:
                    raise PreparationPending('Unqualified local feature schema')
                for name, scalar in row.items():
                    if scalar is None:
                        continue
                    if name == 'aa':
                        if type(scalar) is not str or len(scalar) != 1 or scalar not in amino_acids:
                            raise PreparationPending('Invalid residue character')
                    elif name == 'missing':
                        if type(scalar) is not bool:
                            raise PreparationPending('Missing flag must be boolean')
                    else:
                        number(scalar, integer=name in local_counts)
        elif key == 'sequence':
            if type(item) is not str or len(item) > 100000 or not set(item) <= amino_acids:
                raise PreparationPending('Only amino-acid sequence is allowed')
        elif key == 'input_kind':
            if type(item) is not str or item not in (
                    'W', 'S', 'hard', 'public_restoration', 'synthetic', 'real',
                    'ws280', 'hard83', 'kortemme_ngk', 'native_hard_construction'):
                raise PreparationPending('Unknown input-kind enum')
        elif key in ('loop_intervals', 'loop_lengths'):
            integers(item, interval=key == 'loop_intervals')
        elif key == 'geometry_valid':
            if type(item) is not bool:
                raise PreparationPending('Geometry flag must be boolean or missing')
        else:
            number(item, integer=key in counts)
            if key == 'db_closed_fraction' and not 0 <= item <= 1:
                raise PreparationPending('Invalid closure fraction')
        result[key] = deepcopy(item)
    canonical(result)
    return result

def check_binding(value):
    if type(value) is not dict or set(value) != DIGEST_FIELDS:
        raise PreparationPending('Full source/topology/loops/RNG/context identity required')
    return {key: checked_hash(value[key]) for key in sorted(DIGEST_FIELDS)}


@dataclass
class State:
    binding: dict
    features: dict
    payload: object = field(repr=False, default=None)  # private native state/handle

    def validate(self):
        check_binding(self.binding)
        public_features(self.features)
        return self


@dataclass(frozen=True)
class Capability:
    name: str
    profile: str
    qualification_sha256: str
    runtime_sha256: str
    implementation_sha256: str
    logical_work: float
    max_outputs: int
    parameters: dict = field(default_factory=dict)
    database_sha256: str | None = None

    @property
    def token(self):
        return self.name + ':' + self.profile

    def validate(self):
        if self.name not in ACTIONS or not self.profile or ':' in self.profile:
            raise PreparationPending('Unknown operation/profile')
        for value in (self.qualification_sha256, self.runtime_sha256, self.implementation_sha256):
            checked_hash(value)
        if self.name in ('promod3_native', 'promod3_database') and self.database_sha256 is None:
            raise PreparationPending('Exact filtered database identity required')
        if self.database_sha256 is not None:
            checked_hash(self.database_sha256)
        if not finite(self.logical_work) or self.logical_work <= 0:
            raise PreparationPending('Measured, matching-scope operation work required')
        if type(self.max_outputs) is not int or not 1 <= self.max_outputs <= 8:
            raise PreparationPending('Bounded output count required')
        canonical(self.parameters)
        return self


@dataclass
class OperationResult:
    states: list[State]
    logical_work: float
    physical_cpu_seconds: float
    status: str = 'COMPLETED'
    provenance: dict = field(default_factory=dict)
    policy_memory: dict | None = None
    rng_sha256: str | None = None

    def validate(self, cap):
        if self.status not in ('COMPLETED', 'NO_CANDIDATE', 'SCIENTIFIC_FAILURE'):
            raise PreparationPending('Unresolved operation is not a failed structure')
        if not finite(self.logical_work) or self.logical_work <= 0 or self.logical_work > cap.logical_work:
            raise PreparationPending('Result violates reserved work; reconcile full physical costs')
        if not finite(self.physical_cpu_seconds) or self.physical_cpu_seconds < 0:
            raise PreparationPending('Actual CPU receipt missing')
        if len(self.states) > cap.max_outputs or (self.status != 'COMPLETED' and self.states):
            raise PreparationPending('Output/status contract mismatch')
        if self.rng_sha256 is None:
            raise PreparationPending('Operation must report the resulting RNG identity')
        checked_hash(self.rng_sha256)
        controlled = cap.name in ('ngk_refine', 'ngk_rebuild')
        if controlled and self.policy_memory is None:
            raise PreparationPending('Controlled operation must return final policy memory')
        if not controlled and self.policy_memory is not None:
            raise PreparationPending('Policy-independent operation cannot modify policy memory')
        if self.policy_memory is not None:
            try:
                if type(self.policy_memory) is not dict or len(canonical(self.policy_memory).encode()) > 16384:
                    raise PreparationPending('Returned policy memory exceeds the finite JSON contract')
            except (ValueError, TypeError, RecursionError) as exc:
                raise PreparationPending('Invalid returned memory') from exc
        for state in self.states:
            state.validate()
        return self


def operation_key(parent, cap, context):
    """Evaluator results use a separate cache; these are generation identities."""
    check_binding(parent.binding)
    for name in ('host_protocol_sha256', 'policy_sha256', 'budget_sha256', 'memory_sha256'):
        checked_hash(context[name])
    return digest({'parent': parent.binding, 'action': cap.token,
                   'parameters': cap.parameters, 'runtime': cap.runtime_sha256,
                   'implementation': cap.implementation_sha256,
                   'database': cap.database_sha256, 'qualification': cap.qualification_sha256,
                   'work_contract': {'maximum_work': cap.logical_work, 'max_outputs': cap.max_outputs},
                   'execution_context': context})


def route_observation(value):
    """Only the host's public routing schema can cross the policy boundary."""
    keys = {'stage', 'work', 'remaining_work', 'states', 'available_actions', 'history'}
    if type(value) is not dict or set(value) != keys or value['stage'] != 'route':
        raise PreparationPending('Routing observation schema differs')
    for name in ('work', 'remaining_work'):
        if not finite(value[name]) or value[name] < 0:
            raise PreparationPending('Invalid routing work field')
    if type(value['states']) is not list or not 1 <= len(value['states']) <= 9:
        raise PreparationPending('Visited-state pool is missing or oversized')
    slots = set()
    for state in value['states']:
        if type(state) is not dict or set(state) != {'slot', 'source'}:
            raise PreparationPending('State view contains private fields')
        slot = state['slot']
        if type(slot) is not int or slot < 0 or slot in slots:
            raise PreparationPending('Invalid state slot')
        slots.add(slot)
        public_features(state['source'])
    if 0 not in slots:
        raise PreparationPending('Original RAW state must remain available')
    actions = value['available_actions']
    if type(actions) is not list or len(actions) > 64:
        raise PreparationPending('Invalid capability list')
    tokens = set()
    for cap in actions:
        if type(cap) is not dict or set(cap) != {'name', 'token', 'maximum_work', 'max_outputs', 'parent_slots'}:
            raise PreparationPending('Unqualified capability view')
        if cap['name'] not in ACTIONS or type(cap['token']) is not str:
            raise PreparationPending('Unknown action')
        name, sep, profile = cap['token'].partition(':')
        if not sep or name != cap['name'] or not profile or len(profile) > 64 or not all(c.isalnum() or c in '_-' for c in profile):
            raise PreparationPending('Invalid action/profile token')
        if cap['token'] in tokens:
            raise PreparationPending('Duplicate capability token')
        tokens.add(cap['token'])
        if not finite(cap['maximum_work']) or cap['maximum_work'] <= 0:
            raise PreparationPending('Invalid action work reservation')
        if type(cap['max_outputs']) is not int or not 1 <= cap['max_outputs'] <= 8:
            raise PreparationPending('Invalid action output bound')
        parents = cap['parent_slots']
        if type(parents) is not list or any(type(s) is not int or s not in slots for s in parents):
            raise PreparationPending('Invalid action parent scope')
    if type(value['history']) is not list or len(value['history']) > 16:
        raise PreparationPending('Invalid routing history')
    for event in value['history']:
        if type(event) is not dict or set(event) != {'action','parent_slot','result_slots','work','outcome'}:
            raise PreparationPending('Unqualified history fields')
        token = event['action']
        if type(token) is not str or token.partition(':')[0] not in ACTIONS:
            raise PreparationPending('Invalid history action')
        if type(event['parent_slot']) is not int or type(event['result_slots']) is not list or any(type(s) is not int for s in event['result_slots']):
            raise PreparationPending('Invalid history state references')
        if not finite(event['work']) or event['work'] < 0 or event['outcome'] not in ('COMPLETED','NO_CANDIDATE','SCIENTIFIC_FAILURE'):
            raise PreparationPending('Invalid history outcome')
    return deepcopy(value)


def validate_route(answer, observation):
    observation = route_observation(observation)
    if type(answer) is not dict or set(answer) != {'decision', 'memory'}:
        raise InvalidDecision('Return decision and memory')
    try:
        if type(answer['memory']) is not dict or len(canonical(answer['memory']).encode()) > 16384:
            raise InvalidDecision('Finite JSON memory <=16 KiB required')
    except (ValueError, TypeError, RecursionError) as exc:
        raise InvalidDecision('Invalid policy memory') from exc
    d = answer['decision']
    if type(d) is not dict or set(d) != {'action', 'parent_slot', 'keep_slots'}:
        raise InvalidDecision('Routing keys differ')
    slots = {v['slot'] for v in observation['states']}
    if type(d['parent_slot']) is not int or d['parent_slot'] not in slots:
        raise InvalidDecision('Parent/delivery must be a visited state')
    keep = d['keep_slots']
    if type(keep) is not list or any(type(i) is not int for i in keep) or len(set(keep)) != len(keep):
        raise InvalidDecision('Unique retained slots required')
    if not set(keep) <= slots or 0 not in keep or d['parent_slot'] not in keep:
        raise InvalidDecision('Keep RAW slot0 and the requested parent')
    available = {c['token']: c for c in observation['available_actions']}
    if d['action'] != 'deliver':
        if d['action'] not in available:
            raise InvalidDecision('Unqualified, unavailable or unaffordable action')
        if d['parent_slot'] not in available[d['action']]['parent_slots']:
            raise InvalidDecision('Action is not qualified on this parent state')
        if len(keep) + available[d['action']]['max_outputs'] > 9:
            raise InvalidDecision('Release optional slots before requesting more candidates')
    return deepcopy(answer)


class Router:
    """A host-owned state machine; policy sees no native handles or reference data.

    executor(capability, private_parent_state, private_context) is injected.
    It must never mutate the parent: return independent states/handles. Native
    adapters must qualify that contract before registering any capability.
    """
    def __init__(self, raw, capabilities, executor, *, budget, callback_work,
                 protocol_sha256, policy_sha256, clone_state, cache=None):
        raw.validate()
        if not finite(budget) or not finite(callback_work) or callback_work <= 0 or budget <= callback_work:
            raise PreparationPending('Matched budget and callback price required')
        self.capabilities = {c.validate().token: c for c in capabilities}
        if len(self.capabilities) != len(capabilities):
            raise PreparationPending('Duplicate capability')
        self.states = {0: clone_state(raw)}
        self.executor, self.clone_state = executor, clone_state
        self.budget, self.callback_work, self.work = budget, callback_work, 0.
        self.protocol_sha = checked_hash(protocol_sha256)
        self.policy_sha = checked_hash(policy_sha256)
        self.cache = {} if cache is None else cache
        self.history, self.evidence = [], []
        self.memory, self.next_slot = {}, 1
        self.current_rng_sha256 = raw.binding['rng_sha256']
        self.delivered = None
        self.pending_operation = None

    def observation(self):
        actions = [dict(name=c.name, token=c.token, maximum_work=c.logical_work,
                        max_outputs=c.max_outputs, parent_slots=[slot for slot, state in self.states.items()
                            if not hasattr(self.executor, 'available') or self.executor.available(c, state)])
                   for c in self.capabilities.values()
                   if self.work + c.logical_work + self.callback_work <= self.budget]
        actions = [action for action in actions if action['parent_slots']]
        return dict(stage='route', work=self.work, remaining_work=self.budget-self.work,
                    states=[dict(slot=slot, source=public_features(state.features))
                            for slot, state in sorted(self.states.items())],
                    available_actions=actions, history=deepcopy(self.history[-16:]))

    def step(self, decide):
        if self.pending_operation is not None:
            raise PreparationPending('Reconcile original pending operation; do not replay')
        if self.delivered is not None:
            raise InvalidDecision('Trajectory already delivered')
        if self.work + self.callback_work > self.budget:
            raise PreparationPending('Delivery reservation was lost')
        self.work += self.callback_work
        view = dict(event='route', observation=self.observation(), memory=deepcopy(self.memory))
        answer = validate_route(decide(deepcopy(view)), view['observation'])
        self.memory = answer['memory']
        d = answer['decision']
        parent = self.states[d['parent_slot']]
        if d['action'] == 'deliver':
            self.delivered = self.clone_state(parent)
            self.evidence.append(dict(event='deliver', observation=view['observation'],
                                      decision=d, actual_logical_work=self.work))
            return self.delivered
        cap = self.capabilities[d['action']]
        context = dict(host_protocol_sha256=self.protocol_sha, policy_sha256=self.policy_sha,
                       budget_sha256=digest(self.budget), memory_sha256=digest(self.memory),
                       rng_sha256=self.current_rng_sha256)
        # The controlled NGK suffix depends on policy/memory/remaining budget.
        if cap.name in ('ngk_refine', 'ngk_rebuild'):
            context.update(remaining_work=self.budget-self.work-self.callback_work,
                           policy_memory=deepcopy(self.memory), route_history=digest(self.history))
        else:
            # Frozen, policy-independent operations can be shared across policies.
            context['policy_sha256'] = digest('policy-independent')
            context['memory_sha256'] = digest('no-policy-memory')
        key = operation_key(parent, cap, context)
        # ProMod's internal RNG is not restorable by the Rosetta RNG token.
        # Keep each explicit native invocation distinct until that binding exists.
        cacheable = not cap.name.startswith('promod3')
        cached = cacheable and key in self.cache
        self.pending_operation = dict(operation_key=key, action=cap.token, parent=deepcopy(parent.binding))
        if cached:
            result = self.cache[key]
        else:
            result = self.executor(cap, self.clone_state(parent), deepcopy(context))
        result.validate(cap)
        if hasattr(self.executor, 'after_result'):
            self.executor.after_result(result)
        self.current_rng_sha256 = result.rng_sha256
        if result.policy_memory is not None:
            self.memory = deepcopy(result.policy_memory)
        # Logical work is charged even on cache hits; never offer unseen cached outputs.
        self.work += result.logical_work
        self.states = {k:v for k,v in self.states.items() if k in d['keep_slots']}
        new_slots = []
        for state in result.states:
            slot = self.next_slot; self.next_slot += 1
            self.states[slot] = self.clone_state(state)
            new_slots.append(slot)
        if not cached and cacheable:
            self.cache[key] = OperationResult([self.clone_state(s) for s in result.states],
                result.logical_work, result.physical_cpu_seconds, result.status,
                deepcopy(result.provenance), deepcopy(result.policy_memory), result.rng_sha256)
        public_event = dict(action=cap.token, parent_slot=d['parent_slot'],
                            result_slots=new_slots, work=result.logical_work, outcome=result.status)
        self.history.append(public_event)
        self.evidence.append(dict(event='operation', observation=view['observation'], decision=d,
            result=public_event, operation_key=key, parent_binding=deepcopy(parent.binding),
            child_bindings=[deepcopy(s.binding) for s in result.states], cache_hit=cached,
            rng_before=context['rng_sha256'], rng_after=result.rng_sha256,
            memory_before=deepcopy(view['memory']), memory_after=deepcopy(self.memory),
            physical_cpu_seconds=0. if cached else result.physical_cpu_seconds,
            provenance=deepcopy(result.provenance)))
        self.pending_operation = None
        return None
