"""Evaluated NGK policy session and billed callback wiring."""
from copy import deepcopy
from ..controller import digest, PreparationPending
from .decision_trace import DecisionRecorder

class MCSession:
    """One restricted worker's memory survives route -> MC -> route, including caches."""
    def __init__(self, client, context):
        self.client, self.context = client, context

    def __enter__(self):
        memory = deepcopy(self.context['policy_memory'])
        if digest(memory) != self.context['memory_sha256']:
            raise PreparationPending('Input policy memory identity mismatch')
        self.client.memory = memory
        return self.client

    def __exit__(self, *_):
        self.output_memory = deepcopy(self.client.memory)


def run_legacy_refinement(*, r, parent_pose, loops, client, context,
                          scorefxn, observation_builder, prices, work_limit,
                          options=None, event=None, snapshot=None,
                          recorder=None, state_binding=None, observation_tariff=None, cooperative_stop=None, budget_receipt=None):
    """Execute only after BackendRegistry qualification; no implicit prefix replay.

    A NEW fullatom refinement invocation, not a resumed internal MC checkpoint.
    Native preparation/FoldTree cleanup is delegated to the already qualified host.
    The caller restores the current trajectory RNG before entry and saves it after.
    """
    from .legacy_refine import refine_with_cleanup
    from .policy_adapter import LegacyPolicyAdapter
    if recorder is None or state_binding is None:
        raise PreparationPending('Decision-time recorder and exact native state binding are required')
    from .decision_trace import RecordingClient
    box={}
    recorded=RecordingClient(client,recorder,lambda: (
        state_binding(box['host'],'last'),state_binding(box['host'],'working')))
    def on_event(value,host):
        if value.get('event') == 'acceptance':
            recorder.resolve_acceptance(step=value['step'],
                child_binding=state_binding(host,'last'),accepted=value['accepted'])
        if event is not None:event(value,host)
    session = MCSession(client, context)
    with session:
        adapter = LegacyPolicyAdapter(recorded)
        # Existing refine_with_cleanup does not bind adapters automatically.
        class BoundAdapter:
            def __call__(self, observation, memory):
                return adapter(observation, memory)
        def observe(host, view):
            box['host']=host
            if adapter.host is None:
                adapter.bind(host)
            return observation_builder(host, view)
        refine = refine_with_cleanup
        if observation_tariff is not None:
            from functools import partial
            from .observation_billing import refine_with_billing
            refine = partial(refine_with_billing, observer=observation_builder, tariff=observation_tariff)
            if cooperative_stop is not None:
                from .budgeted_refinement import refine_with_budget
                refine = partial(refine_with_budget,observer=observation_builder,tariff=observation_tariff,
                                 cooperative_stop=cooperative_stop,budget_receipt=budget_receipt)
        host = refine(r, parent_pose, loops, scorefxn=scorefxn,
            controller=BoundAdapter(), observation_builder=observe,
            prices=prices, work_limit=work_limit, options=options,
            event=on_event, snapshot=snapshot)
    return host, session.output_memory
