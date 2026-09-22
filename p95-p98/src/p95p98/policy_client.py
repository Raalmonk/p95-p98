"""Opt-in routing client reusing the existing isolated policy interpreter.

No new candidate execution mechanism or relaxed Python permissions. Import is inert.
"""
from pathlib import Path
import copy
import sys
import time

from .policy_runtime.client import PolicyClient
from .policy_runtime.core import PolicyRuntimeError
from .policy_contract import _memory
from .controller import validate_route, route_observation


class RoutingPolicyClient(PolicyClient):
    def decide(self, event, observation, *, capabilities=None, populated_slots=()):
        if event != 'route':
            result = super().decide(event, observation, capabilities=capabilities,
                                    populated_slots=populated_slots)
            if (event == 'pre_proposal' and result['decision']['loop_index'] is not None
                    and observation.get('site') != 'choose_loop'):
                self.close()
                raise PolicyRuntimeError('INVALID_POLICY: loop choice outside choose_loop')
            return result
        observation = route_observation(observation)
        if not self.lock.acquire(blocking=False):
            raise PolicyRuntimeError('Concurrent policy calls are not allowed')
        begin = time.monotonic()
        try:
            self.serial += 1
            response = self._exchange({'serial': self.serial,
                'view': {'event': 'route', 'observation': copy.deepcopy(observation),
                         'memory': copy.deepcopy(self.memory)}})
            if response.get('serial') != self.serial or response.get('ok') is not True:
                raise PolicyRuntimeError('Routing candidate execution failed')
            self.cpu_seconds += response['cpu_s']
            answer = validate_route(response['value'], observation)
            self.memory = _memory(answer['memory'])
            return {'event': event, **answer}
        except BaseException:
            self.close()
            raise
        finally:
            self.wall_seconds += time.monotonic() - begin
            self.lock.release()

    def decide_view(self, view):
        # Router and MC callbacks must use this same explicit memory, not two copies.
        self.memory = _memory(view['memory'])
        answer = self.decide('route', view['observation'])
        return {key: answer[key] for key in ('decision', 'memory')}
