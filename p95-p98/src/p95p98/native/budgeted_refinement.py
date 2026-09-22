"""Physical stopping around the unchanged, calibrated observation billing."""
import time
from importlib import import_module
from .observation_billing import priced_host

def budgeted_host(base, observer, tariff, cooperative_stop, budget_receipt=None):
    SafeStop=import_module(base.__module__).SafeStop
    class BudgetedHost(priced_host(base,observer,tariff)):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            if budget_receipt is not None:
                original=self.progress
                def progress(marker):
                    budget_receipt(self,marker)
                    original(marker)
                self.progress=progress
        def operation(self,name,call):
            if not self.finalizing and self.mc is not None:
                estimate=self.cpu.get(name,0.)/max(1,self.counts.get(name,0))
                if cooperative_stop.should_stop(name,estimate):
                    self.stopped,self.delivery=True,'last'
                    self.counts['physical_cooperative_stop']+=1
                    self.event(dict(event='physical_cooperative_stop',next_operation=name),self)
                    raise SafeStop()
                actual_call=call
                def call():
                    begin=time.process_time()
                    try:return actual_call()
                    finally:cooperative_stop.note_completed(name,time.process_time()-begin)
            return super().operation(name,call)
    return BudgetedHost

def refine_with_budget(r,pose,loops,*,observer,tariff,cooperative_stop,budget_receipt=None,**kwargs):
    from .legacy_refine import LegacyRefineHost
    original_tree=r.core.kinematics.FoldTree(pose.fold_tree())
    tree=r.core.kinematics.FoldTree()
    r.protocols.loops.fold_tree_from_loops(pose,loops,tree,True)
    pose.fold_tree(tree)
    try:
        host=budgeted_host(LegacyRefineHost,observer,tariff,cooperative_stop,budget_receipt)(r,pose,loops,**kwargs)
        host.run()
        return host
    finally:
        r.protocols.loops.remove_cutpoint_variants(pose)
        pose.fold_tree(original_tree)
