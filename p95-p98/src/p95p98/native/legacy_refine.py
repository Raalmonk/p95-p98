"""Explicit scheduling of Rosetta 5e498f1409 legacy LoopMover_Refine_KIC.

All conformational operations and MC state updates use the installed native
legacy kernels. This implementation is a qualification candidate, not an
equivalence claim. It deliberately preserves original float32 annealing and
MoveMap copy behavior. No modern KicMover is used.

Controller receives only an observation dict and returns a dict. Its hook is
called before operations (schedule) and immediately before all four native
acceptance sites (acceptance). A trusted observation_builder can add source-only
features. Event callbacks and snapshot callbacks are host-side, not policy APIs.
"""
from __future__ import annotations

import copy
import ctypes
import ctypes.util
import math
import struct
import time
from collections import Counter, deque


ROSETTA_VERSION = "2026.03+releasequarterly.5e498f1409"


def f32(value):
    return struct.unpack("f", struct.pack("f", value))[0]


def powf(a, b):
    lib = ctypes.CDLL(ctypes.util.find_library("m"))
    fn = lib.powf
    fn.argtypes = [ctypes.c_float, ctypes.c_float]
    fn.restype = ctypes.c_float
    return float(fn(a, b))


class SafeStop(Exception):
    pass


def make_loops(r, definitions):
    loops = r.protocols.loops.Loops()
    for x in definitions:
        loops.add_loop(r.protocols.loops.Loop(
            x["start"], x["stop"], x["cut"], x.get("skip", 0.0), x.get("extended", False)))
    return loops


class LegacyRefineHost:
    """One continuous fullatom stage. Normal callbacks never restore RNG."""

    def __init__(self, r, pose, loops, scorefxn=None, controller=None,
                 observation_builder=None, event=None, snapshot=None,
                 options=None, work_limit=None, prices=None, progress=None):
        if str(r.utility.Version.version()) != ROSETTA_VERSION:
            raise ValueError("Legacy runtime version mismatch")
        self.r, self.pose, self.loops = r, pose, loops
        self.controller = controller
        self.observation_builder = observation_builder
        self.event = event or (lambda event, host: None)
        self.progress = progress or (lambda name: None)
        self.snapshot = snapshot or (lambda site, host: None)
        self.opts = self.read_options(options or {})
        self.base_score = (scorefxn or r.protocols.loops.get_fa_scorefxn()).clone()
        self.fixed_score = self.base_score.clone()
        self.local_score = self.base_score.clone()
        self.min_score = self.local_score.clone()
        self.memory = {}
        self.archive = {}
        self.archive_meta = {}
        self.history = deque(maxlen=16)
        self.counts = Counter()
        self.cpu = Counter()
        self.outer = self.inner = self.round = self.score_epoch = 0
        self.step = 0
        self.delivery = None
        self.stopped = False
        self.work_limit = work_limit
        self.prices = dict(prices or {})
        self.work = 0.0
        self.finalizing = False
        if (work_limit is not None and controller is not None and
                work_limit < self.prices.get("observe_state", 0.0)+self.prices.get("controller", 0.0)):
            raise ValueError("Budget cannot reserve the terminal observation and delivery callback")
        self.mc = None
        self.last_context = {}

    def read_options(self, overrides):
        o = self.r.basic.options
        kinds = {
            "boolean": ["fix_natsc", "kic_recover_last", "kic_min_after_repack",
                        "optimize_only_kic_region_sidechains_after_move", "fast",
                        "kic_rama2b", "ramp_fa_rep", "ramp_rama", "kic_with_cartmin",
                        "fix_ca_bond_angles", "nonpivot_torsion_sampling", "legacy_kic",
                        "taboo_in_fa", "vicinity_sampling"],
            "integer": ["refine_outer_cycles", "kic_max_seglen", "kic_num_rotamer_trials"],
            "real": ["neighbor_dist", "refine_init_temp", "refine_final_temp"],
        }
        out = {name: getattr(o, "get_" + kind + "_option")("loops:" + name)
               for kind, names in kinds.items() for name in names}
        # Original source uses 200 unless max_inner_cycles.user(), whose boolean
        # is not bound. Callers must explicitly carry that frozen override.
        out.update(max_inner_cycles=200, repack_period=20)
        out.update(overrides)
        if o.get_boolean_option("run:test_cycles"):
            raise ValueError("test_cycles is not a full legacy protocol")
        if out["taboo_in_fa"] or out["vicinity_sampling"]:
            raise ValueError("This host qualifies the frozen Rama2b native mode first")
        if o.get_string_option("loops:restrict_kic_sampling_to_torsion_string"):
            raise ValueError("Torsion-restricted mode is outside the frozen host")
        if o.get_boolean_option("loops:derive_torsion_string_from_native_pose"):
            raise ValueError("Native-derived torsion string is not source-only")
        if out["fast"] or out["legacy_kic"]:
            raise ValueError("Frozen NGK requires non-fast next-generation settings")
        if not out["kic_rama2b"]:
            raise ValueError("Frozen NGK requires Rama2b")
        return out

    def weights(self, score):
        r = self.r
        return {str(term): float(score.get_weight(term))
                for term in score.get_nonzero_weighted_scoretypes()}

    def context(self, site, phase, **extra):
        result = dict(stage="fullatom_legacy_ngk", site=site, phase=phase,
                      outer=self.outer, inner=self.inner, round=self.round,
                      score_epoch=self.score_epoch, step=self.step,
                      counts=dict(self.counts), work=self.work,
                      remaining_work=None if self.work_limit is None else self.work_limit-self.work,
                      history=list(self.history), archive=copy.deepcopy(self.archive_meta),
                      native_temperature=getattr(self, "temperature", None),
                      proposal_weights=self.weights(self.local_score),
                      acceptance_weights=self.weights(self.mc.score_function()) if self.mc else None)
        result.update(extra)
        return result

    def decide(self, observation):
        if self.controller is None:
            return {}
        before = time.process_time()
        try:
            if self.observation_builder:
                def observe():
                    charged_context = dict(observation, counts=dict(self.counts), work=self.work,
                        remaining_work=None if self.work_limit is None else self.work_limit-self.work)
                    return self.observation_builder(self, charged_context)
                observation = self.operation("observe_state", observe)
            result = self.controller(copy.deepcopy(observation), self.memory)
            if result is None:
                result = {}
            if not isinstance(result, dict):
                raise TypeError("Controller must return a dict")
            return result
        finally:
            self.cpu["observation_controller"] += time.process_time()-before

    def save(self, slot, which="current"):
        slot = int(slot)
        if not 0 <= slot < 8:
            raise ValueError("Archive slot must be 0..7")
        if which == "current":
            pose = self.pose
        elif which == "last":
            pose = self.mc.last_accepted_pose()
        elif which == "low":
            pose = self.mc.lowest_score_pose()
        else:
            raise ValueError("Only actual current/last/low states can be saved")
        self.archive[slot] = self.operation("archive_save", pose.clone)
        self.archive_meta[slot] = dict(step=self.step, score_epoch=self.score_epoch,
                                      work=self.work, source=which)

    def restore(self, slot):
        def apply_restore():
            if slot == "low":
                pose = self.mc.lowest_score_pose().clone()
            elif slot == "last":
                pose = self.mc.last_accepted_pose().clone()
            else:
                pose = self.archive[int(slot)].clone()
            self.pose.assign(pose)
            # Reset last/low under this epoch, without resetting RNG, counters,
            # temperature, schedule or consumed work. Previous native low must
            # be archived before restore if the policy wants to retain it.
            self.mc.reset(self.pose)
        self.operation("restore", apply_restore)
        self.event(dict(event="restore", slot=slot, **self.context("restore", "done")), self)

    def control_state(self, decision, allow_restore):
        if "save" in decision:
            save = decision["save"]
            if isinstance(save, int):
                self.save(save)
            else:
                self.save(save["slot"], save.get("source", "current"))
        if "restore" in decision:
            if not allow_restore:
                raise ValueError("Restore is allowed before an operation, not during acceptance")
            self.restore(decision["restore"])
        if decision.get("stop"):
            self.delivery = decision.get("deliver", "last")
            self.stopped = True
            self.counts["safe_stop"] += 1
            raise SafeStop()

    def before(self, site, **extra):
        self.last_context = self.context(site, "pre_proposal", **extra)
        decision = self.decide(self.last_context)
        self.control_state(decision, True)
        self.snapshot(site, self)
        return decision

    def operation(self, name, call):
        price = self.prices.get(name, 0.0)
        terminal_reserve = (self.prices.get("observe_state", 0.0)+self.prices.get("controller", 0.0)
                            if self.controller is not None and not self.finalizing else 0.0)
        if self.work_limit is not None and self.work + price + terminal_reserve > self.work_limit:
            self.stopped, self.delivery = True, "last"
            self.counts["budget_stop"] += 1
            raise SafeStop()
        self.counts[name] += 1
        self.work += price
        self.progress("operation:"+name+":started")
        start = time.process_time()
        try:
            result = call()
            self.progress("operation:"+name+":completed")
            return result
        finally:
            self.cpu[name] += time.process_time()-start

    def accept(self, site, move_type):
        # Observe using the same score function for current and candidate. On
        # initial repack this is deliberately the MC clone from before ramping.
        self.step += 1
        score = self.mc.score_function()(self.pose)
        current = self.mc.last_accepted_score()
        observation = self.context(site, "post_proposal", candidate_energy=score,
                                   current_energy=current, energy_delta=score-current,
                                   lowest_energy=self.mc.lowest_score())
        self.event(dict(event="pre_mc_candidate", **observation), self)
        decision = self.decide(observation)
        # Save candidate is permitted; restoration/stop follows MC resolution.
        save = decision.pop("save", None)
        if save is not None:
            self.control_state({"save": save}, False)
        mode = decision.get("acceptance", "native")
        scale = float(decision.get("temperature_scale", 1.0))
        if not math.isfinite(scale) or not 0.5 <= scale <= 2.0:
            raise ValueError("Acceptance temperature multiplier must be within 0.5..2")
        self.mc.set_temperature(self.temperature*scale)
        if mode == "native":
            accepted = self.mc.boltzmann(self.pose, move_type)
        elif mode == "probability":
            if "temperature_scale" in decision:
                raise ValueError("Direct acceptance probability does not combine with temperature control")
            probability = float(decision["probability"])
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise ValueError("Acceptance probability must be within 0..1")
            cancel = (score-current)/self.mc.temperature()
            accepted = self.mc.boltzmann(self.pose, score, move_type, probability, cancel)
        else:
            raise ValueError("Unknown acceptance mode")
        self.mc.set_temperature(self.temperature)
        self.counts["mc_trials"] += 1
        self.counts["mc_accepts"] += int(accepted)
        record = dict(site=site, step=self.step, accepted=bool(accepted),
                      candidate_energy=score, current_energy=current,
                      last_energy=self.mc.last_accepted_score(),
                      lowest_energy=self.mc.lowest_score(), score_epoch=self.score_epoch,
                      outer=self.outer, inner=self.inner, round=self.round)
        self.history.append(record)
        self.event(dict(event="acceptance", **record), self)
        self.control_state(decision, False)
        self.snapshot(site+":resolved", self)
        return accepted

    def setup(self):
        self.progress("setup:begin")
        r, p, o = self.r, self.pose, self.opts
        if r.core.pose.symmetry.is_symmetric(p):
            raise ValueError("The frozen TRAIN host uses nonsymmetric poses")
        # Installed wheel's Loops iterator segfaults; its indexed binding is
        # valid and preserves the C++ vector1 iteration order.
        for loop_index in range(1, self.loops.size()+1):
            loop = self.loops[loop_index]
            cut = loop.cut()
            if cut != p.size():
                changed = False
                for index, variant in [(cut, r.core.chemical.CUTPOINT_LOWER),
                                       (cut+1, r.core.chemical.CUTPOINT_UPPER)]:
                    if not p.residue(index).has_variant_type(variant):
                        r.core.pose.add_variant_type_to_pose_residue(p, variant, index)
                        changed = True
                if changed:
                    a, b = p.residue(cut), p.residue(cut+1)
                    p.conformation().declare_chemical_bond(
                        cut, a.atom_name(a.upper_connect_atom()),
                        cut+1, b.atom_name(b.lower_connect_atom()))
        self.progress("setup:variants_ready")
        sc = r.core.scoring
        if self.min_score.get_weight(sc.occ_sol_exact) > 0:
            self.min_score.set_weight(sc.fa_sol, 0.65)
            self.min_score.set_weight(sc.occ_sol_exact, 0.0)
        for score in [self.base_score, self.min_score, self.local_score]:
            r.protocols.loops.loop_mover.loops_set_chainbreak_weight(score, 1)
        for score in [self.min_score, self.local_score]:
            score.set_weight(sc.rama2b, score.get_weight(sc.rama))
            score.set_weight(sc.rama, 0.0)
        self.outer_cycles = int(o["refine_outer_cycles"])
        self.inner_cycles = min(int(o["max_inner_cycles"]), 10*self.loops.loop_size())
        self.temperature = f32(o["refine_init_temp"])
        final = f32(o["refine_final_temp"])
        self.gamma = powf(f32(final/self.temperature),
                         f32(1.0/(self.outer_cycles*self.inner_cycles)))
        self.mc = r.protocols.moves.MonteCarlo(p, self.local_score, self.temperature)
        self.progress("setup:mc_ready")
        self.minimizer = r.protocols.minimization_packing.MinMover()
        self.minimizer.score_function(self.min_score)
        self.minimizer.min_type("lbfgs_armijo_nonmonotone")
        self.minimizer.tolerance(0.001)
        self.minimizer.nb_list(True)
        self.minimizer.deriv_check(False)
        self.minimizer.cartesian(o["kic_with_cartmin"])
        self.progress("setup:minimizer_ready")
        tf = r.core.pack.task.TaskFactory()
        tf.push_back(r.core.pack.task.operation.InitializeFromCommandline())
        tf.push_back(r.core.pack.task.operation.IncludeCurrent())
        self.task_factory = tf
        self.repack_task = tf.create_task_and_apply_taskoperations(p)
        self.repack_task.set_bump_check(True)
        self.repack_task.restrict_to_repacking()
        self.progress("setup:repack_task_ready")
        k = r.protocols.loops.loop_closure.kinematic_closure
        self.kic = k.KinematicMover()
        self.progress("setup:kic_ready")
        self.perturber = k.NeighborDependentTorsionSamplingKinematicPerturber(
            self.kic.perturber().kinmover())
        self.perturber.set_vary_ca_bond_angles(not o["fix_ca_bond_angles"])
        self.kic.set_perturber(self.perturber)
        self.progress("setup:perturber_ready")
        self.kic.set_vary_bondangles(True)
        self.kic.set_sample_nonpivot_torsions(o["nonpivot_torsion_sampling"])
        self.kic.set_rama_check(True)
        self.orig_weights = {(kind, term): score.get_weight(term)
                             for kind, score in [("local", self.local_score), ("min", self.min_score)]
                             for term in [sc.fa_rep, sc.rama, sc.rama2b]}
        self.ramp(self.outer_cycles+1)
        self.progress("setup:complete")

    def ramp(self, denominator):
        sc = self.r.core.scoring
        for kind, score in [("local", self.local_score), ("min", self.min_score)]:
            terms = ([sc.fa_rep] if self.opts["ramp_fa_rep"] else [])
            terms += ([sc.rama, sc.rama2b] if self.opts["ramp_rama"] else [])
            for term in terms:
                score.set_weight(term, self.orig_weights[kind, term]/denominator)

    def move_map(self, loops):
        mm = self.r.core.kinematics.MoveMap()
        self.r.protocols.loops.loops_set_move_map(
            self.pose, loops, self.opts["fix_natsc"], mm, self.opts["neighbor_dist"])
        return mm

    def mask(self, loops):
        return self.r.protocols.loops.select_loop_residues(
            self.pose, loops, not self.opts["fix_natsc"], self.opts["neighbor_dist"])

    def update_vectors(self):
        self.move_maps, self.allow_vectors = {}, {}
        for index in range(1, self.loops.size()+1):
            loops = self.r.protocols.loops.Loops()
            loops.add_loop(self.loops[index])
            self.move_maps[index] = self.move_map(loops)
            self.allow_vectors[index] = self.mask(loops)

    def minimize(self, mm, site):
        decision = self.before(site)
        if decision.get("skip", False):
            self.counts["skipped_minimize"] += 1
            return
        self.minimizer.movemap(mm)
        self.minimizer.score_function(self.min_score)
        self.operation("minimize", lambda: self.minimizer.apply(self.pose))

    def initial_repack(self):
        r = self.r
        self.progress("initial_repack:before_context")
        decision = self.before("initial_repack")
        self.progress("initial_repack:after_context")
        self.local_score(self.pose)
        self.all_mask = self.mask(self.loops)
        self.repack_task.restrict_to_residues(self.all_mask)
        if not decision.get("skip", False):
            self.operation("repack", lambda: r.core.pack.pack_rotamers(
                self.pose, self.local_score, self.repack_task))
        else:
            self.counts["skipped_repack"] += 1
        self.rot_task = self.task_factory.create_task_and_apply_taskoperations(self.pose)
        self.rot_task.restrict_to_repacking()
        self.rot_task.set_bump_check(True)
        self.rot_task.restrict_to_residues(self.all_mask)
        self.pose.update_residue_neighbors()
        self.all_mm = self.move_map(self.loops)
        # C++ allocates a COPY here, not a pointer alias to all_mm. Later
        # all_mm refreshes do not change this initial minimizer MoveMap.
        self.all_mm_op = r.core.kinematics.MoveMap(self.all_mm)
        self.minimize(self.all_mm_op, "initial_minimize")
        self.accept("initial_repack", "repack")
        self.update_vectors()

    def repack(self, site):
        d = self.before(site)
        if d.get("skip", False):
            self.counts["skipped_repack"] += 1
            return
        self.update_vectors()
        self.all_mm = self.move_map(self.loops)
        # The source reuses this output vector. select_loop_residues does not
        # clear it: neighbor expansion accumulates over repack sites. Its
        # returning overload would silently reset the native mask here.
        self.r.protocols.loops.select_loop_residues(
            self.pose, self.loops, not self.opts["fix_natsc"], self.all_mask,
            self.opts["neighbor_dist"])
        self.repack_task.restrict_to_residues(self.all_mask)
        self.rot_task.restrict_to_residues(self.all_mask)
        self.operation("repack", lambda: self.r.core.pack.pack_rotamers(
            self.pose, self.local_score, self.repack_task))
        self.local_score(self.pose)  # native verbose score after repack
        if self.opts["kic_min_after_repack"]:
            self.minimize(self.all_mm_op, site+":minimize")
        self.accept(site, "repack")
        self.local_score(self.pose)

    def loop_setup(self, index):
        r = self.r
        loop = self.loops[index]
        self.kic.set_loop_begin_and_end(loop.start(), loop.stop())
        sequence = r.utility.vector1_core_chemical_AA()
        for i in range(loop.start(), loop.stop()+1):
            sequence.append(self.pose.aa(i))
        self.kic.update_sequence(sequence)
        cur_mm = r.core.kinematics.MoveMap(self.move_maps[index])
        cur_mm_op = r.core.kinematics.MoveMap(cur_mm)
        self.rot_task.restrict_to_residues(self.allow_vectors[index])
        return loop, cur_mm, cur_mm_op

    def kinematic_round(self, loop, cur_mm, cur_mm_op):
        r = self.r
        d = self.before("kic", loop_start=loop.start(), loop_stop=loop.stop())
        if d.get("skip", False):
            self.counts["skipped_kic"] += 1
            return
        rng = r.numeric.random.rg()
        begin, end, maxlen = loop.start(), loop.stop(), self.opts["kic_max_seglen"]
        if self.inner % 2 == 0:
            start = rng.random_range(begin, end-2)
            stop = rng.random_range(start+2, min(start+maxlen-1, end))
        else:
            stop = rng.random_range(begin+2, end)
            start = rng.random_range(max(stop-min(maxlen, stop)+1, begin), stop-2)
        middle = start+(stop-start)//2
        self.kic.set_pivots(start, middle, stop)
        self.kic.set_temperature(self.temperature)
        self.operation("kic", lambda: self.kic.apply(self.pose))
        succeeded = self.kic.last_move_succeeded()
        self.counts["kic_success"] += int(succeeded)
        self.event(dict(event="kic_proposal", succeeded=bool(succeeded),
                        pivots=[start, middle, stop], **self.context("kic", "proposed")), self)
        if not succeeded:
            return
        if self.opts["optimize_only_kic_region_sidechains_after_move"]:
            segment = r.protocols.loops.Loop(start, stop, start)
            mask = r.protocols.loops.select_loop_residues(
                self.pose, segment, True, self.opts["neighbor_dist"])
            self.rot_task.restrict_to_residues(mask)
            segments = r.protocols.loops.Loops()
            segments.add_loop(segment)
            r.protocols.loops.loops_set_move_map(
                self.pose, segments, self.opts["fix_natsc"], cur_mm, self.opts["neighbor_dist"])
            # Keep cur_mm_op's native copy semantics.
        if self.inner % self.opts["repack_period"] == 0:
            self.repack("inner_repack")
        d = self.before("rotamer_trials")
        if not d.get("skip", False):
            for _ in range(self.opts["kic_num_rotamer_trials"]):
                self.operation("rotamer_trials", lambda: r.core.pack.rotamer_trials(
                    self.pose, self.local_score, self.rot_task))
                self.pose.update_residue_neighbors()
        else:
            self.counts["skipped_rotamer_trials"] += 1
        self.minimize(cur_mm_op, "kic_minimize")
        if self.accept("kic_round_"+str(self.round), "kic_refine_r"+str(self.round)):
            self.local_score(self.pose)

    def run(self):
        self.setup()
        try:
            self.initial_repack()
            for i in range(1, self.outer_cycles+1):
                self.outer, self.score_epoch = i, i
                for score in [self.base_score, self.min_score, self.local_score]:
                    self.r.protocols.loops.loop_mover.loops_set_chainbreak_weight(score, i)
                self.ramp(self.outer_cycles-i+1)
                self.mc.score_function(self.local_score)
                if not self.opts["kic_recover_last"]:
                    self.mc.recover_low(self.pose)
                self.local_score(self.pose)
                for j in range(1, self.inner_cycles+1):
                    self.inner, self.round = j, 0
                    self.temperature = f32(self.temperature*self.gamma)
                    self.mc.set_temperature(self.temperature)
                    d = self.before("choose_loop")
                    index = (int(d["loop_index"]) if "loop_index" in d else
                             self.r.numeric.random.rg().random_range(1, self.loops.size()))
                    if not 1 <= index <= self.loops.size():
                        raise ValueError("loop_index outside declared loops")
                    loop, cur_mm, cur_mm_op = self.loop_setup(index)
                    for trial in [1, 2]:
                        self.round = trial
                        self.kinematic_round(loop, cur_mm, cur_mm_op)
                    if j == self.inner_cycles:
                        self.repack("outer_repack")
        except SafeStop:
            pass
        self.finalizing = True
        final_decision = self.decide(self.context("terminal", "deliver"))
        if "deliver" in final_decision:
            self.delivery = final_decision["deliver"]
        if self.delivery is None:
            chosen = (self.mc.last_accepted_pose() if self.opts["kic_recover_last"]
                      else self.mc.lowest_score_pose())
        elif self.delivery == "last":
            chosen = self.mc.last_accepted_pose()
        elif self.delivery == "low":
            chosen = self.mc.lowest_score_pose()
        else:
            chosen = self.archive[int(self.delivery)]
        self.pose.assign(chosen)
        self.event(dict(event="terminal", stopped=self.stopped, work=self.work,
                        counts=dict(self.counts), cpu=dict(self.cpu)), self)
        return self.pose


def refine_with_cleanup(r, pose, loops, **kwargs):
    """The original LoopRelaxMover refinement topology envelope."""
    original_tree = r.core.kinematics.FoldTree(pose.fold_tree())
    tree = r.core.kinematics.FoldTree()
    r.protocols.loops.fold_tree_from_loops(pose, loops, tree, True)
    pose.fold_tree(tree)
    host = LegacyRefineHost(r, pose, loops, **kwargs)
    try:
        host.run()
    finally:
        r.protocols.loops.remove_cutpoint_variants(pose)
        pose.fold_tree(original_tree)
    return host
