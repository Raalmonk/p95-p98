"""Map the strict public policy contract onto the legacy host callbacks.

Construction: adapter = LegacyPolicyAdapter(client); pass controller=adapter to
LegacyRefineHost, then adapter.bind(host), then host.run(). client.decide is the
persistent restricted worker interface, and owns policy memory validation.
"""
from __future__ import annotations


class LegacyPolicyAdapter:
    def __init__(self, client):
        self.client = client
        self.host = None

    def bind(self, host):
        self.host = host
        return self

    def capabilities(self, observation):
        site = observation["site"]
        return dict(loop_count=self.host.loops.size(), perturbations=["native"],
                    repack=["native", "skip"] if site in (
                        "initial_repack", "inner_repack", "outer_repack") else ["native"],
                    minimize=["native", "skip"] if "minimize" in site else ["native"],
                    direct_probability=True, temperature=True, archive=True, stop=True)

    def request(self, event, observation):
        answer = self.host.operation("controller", lambda: self.client.decide(
            event, observation, capabilities=self.capabilities(observation),
            populated_slots=tuple(self.host.archive)))
        return answer["decision"]

    def __call__(self, observation, unused_memory):
        if self.host is None:
            raise RuntimeError("Policy adapter must be bound before native execution")
        phase, site = observation["phase"], observation["site"]
        if phase == "deliver":
            d = self.request("deliver", observation)
            return {"deliver": {"current": "last", "native_low": "low",
                                "archive": d["slot"]}[d["state"]]}
        if phase == "pre_proposal":
            d = self.request("pre_proposal", observation)
            out = {}
            if d["stop"]:
                return {"stop": True}
            if d["restore_slot"] is not None:
                out["restore"] = d["restore_slot"]
            if d["loop_index"] is not None:
                if site != "choose_loop":
                    raise ValueError("Loop choice is available only at choose_loop")
                out["loop_index"] = d["loop_index"]+1
            if d["repack"] == "skip" or d["minimize"] == "skip":
                out["skip"] = True
            return out
        if phase != "post_proposal":
            raise ValueError("Unknown native decision phase")
        out = {}
        retain = self.request("retain", observation)
        if retain["save_slot"] is not None:
            out["save"] = dict(slot=retain["save_slot"], source={
                "current": "last", "candidate": "current", "native_low": "low"
            }[retain["state"]])
        d = self.request("accept", observation)
        if d["mode"] == "probability":
            out.update(acceptance="probability", probability=d["probability"])
        elif d["mode"] == "temperature":
            out.update(acceptance="native", temperature_scale=d["temperature_multiplier"])
        return out
