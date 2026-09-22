"""Record decision-time source observations without scoring or inventing outcomes."""
from __future__ import annotations
from copy import deepcopy
from ..controller import PreparationPending, check_binding, digest


class DecisionRecorder:
    def __init__(self, *, split='INFERENCE', maximum_details=16):
        if split not in ('TRAIN', 'INFERENCE') or type(maximum_details) is not int or maximum_details < 1:
            raise PreparationPending('Predeclared trace capture required')
        self.split = split
        self.maximum_details=maximum_details;self.records=[];self.counts={};self.total=0
        self.sampled=set()

    def sample_key(self,event,observation):
        total=(observation.get('work') or 0)+(observation.get('remaining_work') or 0)
        progress=(observation.get('work') or 0)/total if total else 0.
        bins=max(1,(self.maximum_details-2)//2)
        bucket=min(bins-1,int(progress*bins))
        return event,bucket

    def want_detail(self,event,observation):
        if event == 'deliver':return len(self.records)<self.maximum_details
        if event not in ('pre_proposal','accept'):return False
        return (len(self.records)<self.maximum_details-1 and
                self.sample_key(event,observation) not in self.sampled)

    def capture(self,event,observation,decision,parent_binding,candidate_binding):
        self.total+=1;self.counts[event]=self.counts.get(event,0)+1
        if not self.want_detail(event,observation):return
        self.sampled.add(self.sample_key(event,observation))
        parent=check_binding(parent_binding);candidate=check_binding(candidate_binding)
        # The same frozen projection used by the actual restricted worker.
        from ..policy_runtime.core import project_source
        from .observations import VIEW_FIELDS
        public=project_source(observation,VIEW_FIELDS)
        self.records.append(dict(kind='legacy_mc',split=self.split,event=event,
            observation_before=public,actual_decision=deepcopy(decision),
            parent_binding=parent,candidate_binding=candidate,child_binding=None,
            outcome_status='NOT_YET_RESOLVED',capture_index=self.total))

    def resolve_acceptance(self, *, step, child_binding, accepted):
        child=check_binding(child_binding)
        for record in reversed(self.records):
            if record['event']=='accept' and record['observation_before']['step']==step:
                if record['outcome_status']!='NOT_YET_RESOLVED':
                    raise PreparationPending('Acceptance event resolved twice')
                record.update(child_binding=child,accepted=bool(accepted),outcome_status='OBSERVED')
                return

    def coverage(self):
        return dict(total_callbacks=self.total,captured_details=len(self.records),
            omitted_details=self.total-len(self.records),event_counts=dict(self.counts),
            selection='predeclared work-progress bins by event plus terminal; no target-outcome selection',
            complete_trajectory_oracle=False)


class RecordingClient:
    def __init__(self,base,recorder,binding_supplier):
        self.base,self.recorder,self.binding_supplier=base,recorder,binding_supplier
    @property
    def memory(self):return self.base.memory
    @memory.setter
    def memory(self,value):self.base.memory=value
    def decide(self,event,observation,**kwargs):
        # Capture exact identities before an action can change a working pose.
        parent,candidate=self.binding_supplier() if self.recorder.want_detail(event,observation) else (None,None)
        answer=self.base.decide(event,observation,**kwargs)
        self.recorder.capture(event,observation,answer['decision'],parent,candidate)
        return answer


def stop_diagnostics(terminal):
    """Legacy missing data remain missing, rather than being inferred as zero."""
    counts=terminal.get('counts')
    if not isinstance(counts,dict):
        return dict(policy_stop=None,budget_stop=None,reason='NOT_RECORDED',delivery_age=None)
    policy=counts.get('safe_stop');budget=counts.get('budget_stop')
    reason=('POLICY_AND_BUDGET' if policy and budget else 'POLICY_STOP' if policy else
            'BUDGET_STOP' if budget else 'NATIVE_SCHEDULE_COMPLETE' if terminal.get('status') in
            ('COMPLETE','NATIVE_COMPLETED') else 'NOT_RECORDED')
    return dict(policy_stop=policy,budget_stop=budget,reason=reason,
        delivery_age=terminal.get('delivery_age'),
        delivery_scope='NOT_RECORDED' if terminal.get('delivery_age') is None else 'RECORDED')
