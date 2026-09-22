"""Prospective remaining-budget NGK contract; not enabled for original five.

Logical work and actual CPU are independent counters. No caller gets a larger
row budget, wall deadline, or permission from importing this module.
"""
import math
import time

def allocate(*, row_budget, logical_spent, cpu_spent, wall_remaining,
             delivery_reserve, callback_reserve, endpoint_logical_reserve,
             physical_budget=None, atomic_cpu=None, atomic_wall=None):
    numbers=(row_budget,logical_spent,cpu_spent,wall_remaining,delivery_reserve,
             callback_reserve,endpoint_logical_reserve)
    if any(not math.isfinite(x) or x<0 for x in numbers):
        raise ValueError('Nonnegative finite independent budget quantities required')
    logical=max(0.,row_budget-delivery_reserve-logical_spent-callback_reserve)
    # floor prevents allocating an RLIMIT integer beyond the remaining CPU.
    cpu=max(0,math.floor((row_budget if physical_budget is None else physical_budget)-delivery_reserve-cpu_spent))
    if atomic_cpu is not None:cpu=min(cpu,atomic_cpu)
    wall=wall_remaining if atomic_wall is None else min(wall_remaining,atomic_wall)
    return dict(contract='NGK_REMAINING_ROW_BUDGET',logical_action_limit=logical,
        physical_cpu_limit=cpu,wall_limit=wall,
        refinement_logical_limit=max(0.,logical-endpoint_logical_reserve),
        can_dispatch=cpu>=1 and logical>endpoint_logical_reserve and wall_remaining>0,
        original_row_budget=row_budget,terminal_cpu_reserve=delivery_reserve)

class CooperativeStop:
    """Stop between completed primitives; no half-finished pose is delivered.

    Predictor is a scheduling estimate only, never the actual CPU ledger or
    logical tariff. RLIMIT plus the parent wall guard remains the hard bound.
    A blocking indivisible primitive can still time out without a candidate.
    """
    def __init__(self,*,cpu_limit,wall_limit,terminal_reserve,cpu_clock=time.process_time,
                 wall_clock=time.monotonic):
        self.cpu_clock,self.wall_clock=cpu_clock,wall_clock
        self.cpu_end=cpu_clock()+cpu_limit
        self.wall_end=wall_clock()+wall_limit
        self.reserve=terminal_reserve
        self.previous={}

    def should_stop(self,name,estimate=0.):
        projected=max(estimate,self.previous.get(name,0.))
        return (self.cpu_end-self.cpu_clock()<=self.reserve+projected or
                self.wall_end-self.wall_clock()<=self.reserve+projected)

    def note_completed(self,name,measured_cpu):
        self.previous[name]=max(self.previous.get(name,0.),measured_cpu)
