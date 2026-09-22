"""Per-state observation billing for the new routing interface only.

Native moves are inherited unchanged. No default or invented numerical prices:
a bound measured tariff is required; the old native-only price book is untouched.
"""
import math
import time
from ..controller import PreparationPending


def quote(observer, host, tariff):
    from .observations import POSE_MUTATING_COUNTS
    required = {'view', 'fresh_state', 'cached_state', 'archive_displacement'}
    if not required <= set(tariff) or tariff.get('status') != 'MEASURED':
        raise PreparationPending('Measured observation tariff is required')
    if any(type(tariff[k]) not in (int,float) or not math.isfinite(tariff[k])
           or tariff[k] <= 0 for k in required):
        raise PreparationPending('Observation prices must be finite and positive')
    keys = {'working': (host.score_epoch, *(host.counts[n] for n in POSE_MUTATING_COUNTS))}
    if host.mc is not None:
        keys['current'] = (host.score_epoch, host.counts['mc_accepts'], host.counts['restore'])
    hits = sum(observer._cache.get(role, (None,))[0] == key for role,key in keys.items())
    fresh = len(keys)-hits
    cost = (tariff['view']+fresh*tariff['fresh_state']+hits*tariff['cached_state']
            +len(host.archive)*tariff['archive_displacement'])
    return dict(logical_work=cost, fresh_states=fresh, cached_states=hits,
                archive_states=len(host.archive))


def priced_host(base, observer, tariff):
    from importlib import import_module
    SafeStop = import_module(base.__module__).SafeStop
    class PricedHost(base):
        def operation(self, name, call):
            if name != 'observe_state':
                return super().operation(name, call)
            receipt = quote(observer, self, tariff)
            maximum = (tariff['view']+2*max(tariff['fresh_state'],tariff['cached_state'])
                       +8*tariff['archive_displacement'])
            if self.prices.get('observe_state',0.) < maximum:
                raise PreparationPending('Terminal observation reservation is not calibrated')
            reserve = (maximum+self.prices.get('controller',0.)
                       if self.controller is not None and not self.finalizing else 0.)
            price = receipt['logical_work']
            if self.work_limit is not None and self.work+price+reserve > self.work_limit:
                self.stopped, self.delivery = True, 'last'
                self.counts['budget_stop'] += 1
                raise SafeStop()
            self.counts[name] += 1
            self.work += price
            self.progress('operation:'+name+':started')
            before_scores = self.counts['observation_score_calls']
            before_hits = self.counts['observation_cache_hits']
            start = time.process_time()
            try:
                result = call()
                if (self.counts['observation_score_calls']-before_scores != 2*receipt['fresh_states']
                        or self.counts['observation_cache_hits']-before_hits != receipt['cached_states']):
                    raise PreparationPending('Observed cache work differs from the charged work')
                self.progress('operation:'+name+':completed')
                return result
            finally:
                self.cpu[name] += time.process_time()-start
                self.event(dict(event='observation_charge', **receipt), self)
    return PricedHost


def refine_with_billing(r, pose, loops, *, observer, tariff, **kwargs):
    from .legacy_refine import LegacyRefineHost
    original_tree = r.core.kinematics.FoldTree(pose.fold_tree())
    tree = r.core.kinematics.FoldTree()
    r.protocols.loops.fold_tree_from_loops(pose, loops, tree, True)
    pose.fold_tree(tree)
    host = None
    try:
        host = priced_host(LegacyRefineHost, observer, tariff)(r, pose, loops, **kwargs)
        host.run()
        return host
    finally:
        r.protocols.loops.remove_cutpoint_variants(pose)
        pose.fold_tree(original_tree)
