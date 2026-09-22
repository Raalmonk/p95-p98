"""Focused bookkeeping tests; no PyRosetta, poses, RNG or biological work."""
from collections import Counter
import unittest

from p95p98.native.legacy_refine import LegacyRefineHost, SafeStop
from p95p98.native.policy_adapter import LegacyPolicyAdapter
from p95p98.native.legacy_protocol import closure_gate


class FakePose:
    def __init__(self, value):
        self.value = value

    def clone(self):
        return FakePose(self.value)

    def assign(self, other):
        self.value = other.value


class FakeMC:
    def __init__(self):
        self.last = FakePose(1)
        self.low = FakePose(0)
        self.resets = 0

    def last_accepted_pose(self):
        return self.last

    def lowest_score_pose(self):
        return self.low

    def reset(self, pose):
        self.last = pose.clone()
        self.low = pose.clone()
        self.resets += 1


def host(prices, budget):
    h = object.__new__(LegacyRefineHost)
    h.controller = lambda observation, memory: {}
    h.prices, h.work_limit, h.work = prices, budget, 0.0
    h.finalizing, h.stopped, h.delivery = False, False, None
    h.counts, h.cpu = Counter(), Counter()
    h.progress = lambda name: None
    h.event = lambda value, host: None
    h.context = lambda site, phase: dict(site=site, phase=phase)
    h.pose, h.mc = FakePose(3), FakeMC()
    h.archive, h.archive_meta = {0: FakePose(7)}, {}
    h.step, h.score_epoch = 4, 2
    return h


class ControlAccounting(unittest.TestCase):
    def test_terminal_observation_is_reserved_and_charged(self):
        h = host(dict(repack=8, observe_state=2), 10)
        called = []
        h.operation("repack", lambda: called.append("repack"))
        with self.assertRaises(SafeStop):
            h.operation("observe_state", lambda: called.append("nonterminal"))
        h.finalizing = True
        h.operation("observe_state", lambda: called.append("terminal"))
        self.assertEqual(called, ["repack", "terminal"])
        self.assertEqual(h.work, 10)
        self.assertEqual(h.counts["observe_state"], 1)

    def test_restore_is_reserved_before_mutation(self):
        h = host(dict(restore=9, observe_state=2), 10)
        with self.assertRaises(SafeStop):
            h.restore(0)
        self.assertEqual(h.pose.value, 3)
        self.assertEqual(h.mc.resets, 0)
        self.assertEqual(h.counts["restore"], 0)

    def test_restore_charges_once_and_resets_active_low(self):
        h = host(dict(restore=3, observe_state=2), 10)
        h.restore(0)
        self.assertEqual(h.work, 3)


        self.assertEqual(h.counts["restore"], 1)
        self.assertEqual(h.mc.resets, 1)
        self.assertEqual(h.pose.value, 7)
        self.assertEqual(h.mc.low.value, 7)

    def test_save_reserves_before_archive_mutation(self):
        h = host(dict(archive_save=9, observe_state=2), 10)
        with self.assertRaises(SafeStop):
            h.save(1)
        self.assertNotIn(1, h.archive)
        self.assertEqual(h.counts["archive_save"], 0)

    def test_save_charges_and_records_postcharge_work(self):
        h = host(dict(archive_save=1, observe_state=2), 10)
        h.save(1, "low")
        self.assertEqual(h.archive[1].value, 0)
        self.assertEqual(h.archive_meta[1]["work"], 1)
        self.assertEqual(h.counts["archive_save"], 1)

    def test_native_controller_none_has_no_policy_reserve(self):
        h = host(dict(repack=10, observe_state=2), 10)
        h.controller = None
        h.operation("repack", lambda: None)
        self.assertEqual(h.work, 10)

    def test_terminal_reserves_both_observation_and_callback(self):
        h = host(dict(repack=7, observe_state=2, controller=1), 10)
        h.operation("repack", lambda: None)
        with self.assertRaises(SafeStop):
            h.operation("controller", lambda: None)
        h.finalizing = True
        h.operation("observe_state", lambda: None)
        h.operation("controller", lambda: None)
        self.assertEqual(h.work, 10)
        self.assertEqual(h.counts["controller"], 1)

    def test_adapter_charges_retain_and_accept_separately(self):
        h = host(dict(observe_state=2, controller=1), 10)
        h.loops = type("Loops", (), {"size": lambda self: 1})()
        calls = []
        class Client:
            def decide(self, event, observation, **kwargs):
                calls.append(event)
                return dict(decision=(dict(save_slot=None, state="current") if event == "retain"
                                      else dict(mode="native")))
        adapter = LegacyPolicyAdapter(Client()).bind(h)
        self.assertEqual(adapter(dict(site="kic_round_1", phase="post_proposal"), {}), {})
        self.assertEqual(calls, ["retain", "accept"])
        self.assertEqual(h.counts["controller"], 2)
        self.assertEqual(h.work, 2)

    def test_adapter_terminal_delivery_uses_reserved_callback(self):
        h = host(dict(observe_state=2, controller=1), 3)
        h.loops = type("Loops", (), {"size": lambda self: 1})()
        h.finalizing = True
        h.operation("observe_state", lambda: None)
        class Client:
            def decide(self, event, observation, **kwargs):
                return dict(decision=dict(state="native_low", slot=None))
        adapter = LegacyPolicyAdapter(Client()).bind(h)
        self.assertEqual(adapter(dict(site="terminal", phase="deliver"), {}), dict(deliver="low"))
        self.assertEqual(h.work, 3)


class ClosureGateParsing(unittest.TestCase):
    def test_final_closed_traversal_after_retry(self):
        trace = "\n".join("result of loop closure:0 success, 3 failure " + str(x)
                          for x in (3, 0, 0))
        self.assertTrue(closure_gate(trace, 0, 0, True)["eligible"])

    def test_final_failed_loop_blocks_refinement(self):
        trace = "\n".join("result of loop closure:0 success, 3 failure " + str(x)
                          for x in (0, 3))
        self.assertFalse(closure_gate(trace, 0, 0, True)["eligible"])

    def test_failed_mover_status_overrides_closure_message(self):
        trace = "result of loop closure:0 success, 3 failure 0"
        self.assertFalse(closure_gate(trace, 1, 0, True)["eligible"])

    def test_warm_start_is_explicit_without_centroid_closure(self):
        self.assertTrue(closure_gate("", 0, 0, False)["eligible"])

    def test_missing_centroid_capture_cannot_infer_success(self):
        with self.assertRaises(RuntimeError):
            closure_gate("", 0, 0, True)


if __name__ == "__main__":
    unittest.main()
