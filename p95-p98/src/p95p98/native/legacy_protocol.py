"""Native LoopRelaxMover prefix plus qualified explicit legacy refinement.

The original native prefix is unchanged apart from deferring refinement and
requesting its original fullatom output. Failed closure retains the original
native endpoint and does not enter the controlled refinement stage.
"""
import re
import time

from .legacy_refine import LegacyRefineHost, make_loops


class PrefixObservationError(RuntimeError):
    """Native operation returned, but host evidence cannot interpret its gate."""


def configure_legacy_tracer(r):
    """The same observer-only tracer settings as the full native qualifiers."""
    tracer = r.basic.TracerOptions()
    tracer.level = 300
    tracer.muted.append("all")
    tracer.unmuted.append("protocols.loops")
    tracer.unmuted.append("protocols.moves.MonteCarlo")
    r.basic.TracerImpl.set_tracer_options(tracer)


def closure_gate(trace, move_status, success_status, rebuild):
    if move_status != success_status:
        return dict(eligible=False, reason="native_prefix_failed", closure_results=[])
    if not rebuild:
        return dict(eligible=True, reason="native_warm_start", closure_results=[])
    results = [int(x) for x in re.findall(
        r"result of loop closure:0 success, 3 failure\s+([0-9]+)", trace)]
    if not results:
        raise PrefixObservationError("Native legacy closure result missing; cannot infer refinement eligibility")
    # IndependentLoopMover immediately breaks on the first failed loop. On
    # another rebuild attempt it starts over. Consequently the final result is
    # zero iff the final attempted traversal closed every selected loop, under
    # the frozen skip=0/no-aborted-loops/no-classic-filter native settings.
    return dict(eligible=results[-1] == 0,
                reason="native_all_loops_closed" if results[-1] == 0 else "native_loops_unclosed",
                closure_results=results)


def prefix(r, pose, definitions, *, rebuild, event=None, preserve=None,
           idealize_after_loop_close_user=False):
    event = event or (lambda value: None)
    configure_legacy_tracer(r)
    loops = make_loops(r, definitions)
    if any(x.get("skip", 0.0) != 0.0 for x in definitions):
        raise ValueError("Frozen native prefix requires no skipped loops")
    # Native source requires .user() AND .value(); its default value is True.
    # The .user() accessor is not bound. Carry provenance from the frozen
    # initializer/options contract, which does not set this option explicitly.
    if (idealize_after_loop_close_user and
            r.basic.options.get_boolean_option("loops:idealize_after_loop_close")):
        raise ValueError("Post-refinement idealization is outside frozen protocol")
    mover = r.protocols.relax.loop.LoopRelaxMover()
    mover.loops(loops)
    mover.refine("no")
    if not rebuild:
        mover.remodel("no")
    if mover.remodel() != ("perturb_kic" if rebuild else "no"):
        raise ValueError("Native prefix remodel setting differs")
    if mover.intermedrelax() != "no" or mover.relax() != "no":
        raise ValueError("Native prefix adds an unqualified relaxation stage")
    # The source constructor uses this identical factory. Holding the pointer
    # exposes its exact post-prefix constraint weights to the refinement host.
    fa_score = r.protocols.loops.get_fa_scorefxn()
    mover.fa_scorefxn(fa_score)
    old_fullatom = r.basic.options.get_boolean_option("out:file:fullatom")
    r.basic.options.set_boolean_option("out:file:fullatom", True)
    capture = r.basic.PyTracer()
    flusher = r.basic.Tracer("ngk_mc_prefix_capture")
    r.basic.Tracer.set_ios_hook(capture, r.basic.Tracer.get_all_channels_string(), True)
    start, cpu = time.monotonic(), time.process_time()
    event(dict(event="native_prefix_started", rebuild=rebuild))
    try:
        mover.apply(pose)
    finally:
        flusher.flush_all_channels()
        capture.flush()
        r.basic.Tracer.set_ios_hook(None, "", True)
        r.basic.options.set_boolean_option("out:file:fullatom", old_fullatom)
    trace = capture.buf()
    result = dict(native_move_status=str(mover.get_last_move_status()),
                  trace=trace, wall_seconds=time.monotonic()-start,
                  process_cpu_seconds=time.process_time()-cpu, native_prefix_applies=1,
                  idealize_after_loop_close_user=idealize_after_loop_close_user)
    used_loops = mover.get_loops()
    # Clear the caller's native-operation marker and save the full live stack
    # before any host interpretation. Tracer/parser faults are not native fails.
    event(dict(event="native_prefix_returned", **result))
    if preserve is not None:
        preserve(dict(pose=pose, loops=used_loops, fa_score=fa_score,
                      mover=mover, result=result))
    result["gate"] = closure_gate(trace, mover.get_last_move_status(), r.protocols.moves.MS_SUCCESS, rebuild)
    event(dict(event="native_prefix_completed", **result))
    return pose, used_loops, fa_score, result


def controlled_protocol(r, pose, definitions, *, rebuild, controller=None,
                        observation_builder=None, event=None, snapshot=None,
                        options=None, work_limit=None, prices=None, progress=None,
                        prefix_event=None, prefix_preserve=None):
    """Caller owns seed, runtime configuration, source loader and resource lease."""
    pose, loops, fa_score, pre = prefix(r, pose, definitions, rebuild=rebuild,
                                       event=prefix_event, preserve=prefix_preserve)
    if not pre["gate"]["eligible"]:
        return pose, None, pre
    original_tree = r.core.kinematics.FoldTree(pose.fold_tree())
    tree = r.core.kinematics.FoldTree()
    r.protocols.loops.fold_tree_from_loops(pose, loops, tree, True)
    pose.fold_tree(tree)
    host = LegacyRefineHost(r, pose, loops, scorefxn=fa_score, controller=controller,
                            observation_builder=observation_builder, event=event,
                            snapshot=snapshot, options=options, work_limit=work_limit,
                            prices=prices, progress=progress)
    if hasattr(controller, "bind"):
        controller.bind(host)
    try:
        host.run()
    finally:
        r.protocols.loops.remove_cutpoint_variants(pose)
        pose.fold_tree(original_tree)
    # Original LoopRelaxMover final score uses the retained fa_score pointer,
    # whose weights are independent of refinement's cloned ramp schedules.
    fa_score(pose)
    return pose, host, pre
