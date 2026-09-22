"""Native legacy NGK whole-trajectory adapter; no endpoint scoring or dispatch.

One isolated worker per arm/case. Caller supplies the frozen corrected raw pose,
restores its original control RNG, captures terminal output, and owns shared56.
Only execute() calls apply(); inspect_runtime() never loads a pose or runs a move.
"""
import copy
import hashlib
import json
import time

ROSETTA_COMMIT = '5e498f1409c68ade56c8ce5842bf79e1b02e8db4'
ROSETTA_VERSION = '2026.03+releasequarterly.5e498f1409'
CAPTURE_COMMIT = '3bc00b98c1b9a7683ac8961119189dc2113e5fff'
CAPTURE_MEMBER = 'protocols/rosetta/legacy/next_gen_kic.flags'
BOOLEAN_OPTIONS = {
    'loops:kic_rama2b': True, 'loops:kic_omega_sampling': True,
    'loops:allow_omega_move': True, 'loops:ramp_fa_rep': True,
    'loops:ramp_rama': True, 'packing:ex1': True,
    'packing:ex2': True, 'packing:ex2aro': False,
}
INTEGER_OPTIONS = {'loops:refine_outer_cycles': 5}
STRING_OPTIONS = {'loops:remodel':'perturb_kic', 'loops:refine':'refine_kic'}
# Read and assert only: explicitly setting some defaults changes Rosetta's
# option.user() branches (notably max_inner_cycles and strict_loops).
DEFAULT_CHECKS = {
    'boolean': {'run:test_cycles':False, 'loops:fix_natsc':False,
        'loops:legacy_kic':False, 'loops:kic_recover_last':False,
        'loops:kic_min_after_repack':True, 'loops:fast':False,
        'loops:strict_loops':False,'corrections:score:use_bicubic_interpolation':True},
    'integer': {'loops:perturb_outer_cycles':5, 'loops:max_inner_cycles':1,
        'loops:repack_period':20, 'loops:max_kic_build_attempts':10000,
        'loops:remodel_kic_attempts':300, 'loops:kic_max_seglen':12,
        'loops:build_attempts':3, 'loops:kic_num_rotamer_trials':1,'packing:extrachi_cutoff':18},
    'real': {'loops:neighbor_dist':10.0,'loops:kic_bump_overlap_factor':0.36,
        'loops:remodel_init_temp':2.0,'loops:remodel_final_temp':1.0,
        'loops:refine_init_temp':1.5,'loops:refine_final_temp':0.5},
    'string': {'loops:intermedrelax':'no','loops:relax':'no',
        'loops:cen_weights':'cen_std','loops:cen_patch':'score4L'},
}
PARAMETERS = {
    'schema':'native-ngk-capture-v1', 'trajectory_count':1,
    'implementation':'protocols.relax.loop.LoopRelaxMover',
    'rosetta_version':ROSETTA_VERSION,'capture_commit':CAPTURE_COMMIT,
    'boolean_options':BOOLEAN_OPTIONS,'integer_options':INTEGER_OPTIONS,
    'string_options':STRING_OPTIONS,'asserted_native_defaults':DEFAULT_CHECKS,
    'loop_definition':'source_raw_start_stop_cut_skip_extend_matched_to_pose_indices',
    'movability':'native_loop_backbone_and_10A_neighbor_sidechains_not_equal_W0_DOF',
    'retention':'native_MC_lowest_score_no_external_selection',
    'inherited_ex2aro':'disabled_to_match_capture_ex1_ex2_only',
    'score_functions':'installed_native_defaults_no_endpoint_score_injection',
    'source_gap_policy':'native_foldtree_must_retain_real_chain_breaks_or_NOT_APPLICABLE',
}


def parameter_sha256():
    return hashlib.sha256(json.dumps(PARAMETERS,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def loop_definitions(row):
    """Retain source loop flags, validating a one-to-one identity match."""
    expected = {tuple(x['residues']) for x in row['loops']}
    found = {}
    for task in row['loop_tasks']:
        for source in task['loops']:
            key = tuple(source['pose_indices'])
            if key not in expected:
                continue
            tokens = source['loop_definition_raw'].split()
            if tokens[0]=='LOOP':tokens=tokens[1:]
            if len(tokens)!=5:raise ValueError('Incomplete source loop definition')
            start,stop,cut = map(int,tokens[:3]);skip=float(tokens[3]);extended=int(tokens[4])
            if (key != tuple(range(start,stop+1)) or not start<=cut<=stop
                    or skip!=0 or extended not in (0,1) or len(key)<3):
                raise ValueError('Source loop not an eligible exact pose-index loop')
            definition = dict(start=start,stop=stop,cut=cut,skip=skip,extended=bool(extended))
            if key in found and found[key]!=definition:raise ValueError('Conflicting source loop definitions')
            found[key]=definition
    if set(found)!=expected:raise ValueError('Missing source loop definition')
    return [found[tuple(x['residues'])] for x in row['loops']]


def work_budget(row):
    lengths = [x['stop']-x['start']+1 for x in loop_definitions(row)]
    return dict(trajectories=1,loop_lengths=lengths,
        centroid_outer_cycles=5,centroid_inner_cycles_per_loop=[min(1000,20*n) for n in lengths],
        fullatom_outer_cycles=5,fullatom_inner_cycles=min(200,10*sum(lengths)),
        fullatom_kinematic_rounds_per_inner=2,initial_closure_max_attempts=10000,
        perturb_kic_attempts_per_inner=300,independent_loop_build_attempts=3,
        looprelax_rebuild_tries=3,repack_period=20,
        realized_work='native branching; retain tracer, elapsed and process CPU; not fixed-action efficiency')


def configure_runtime(rosetta, params):
    if params!=PARAMETERS:raise ValueError('NGK parameters differ from frozen proposal')
    if str(rosetta.utility.Version.version())!=ROSETTA_VERSION:raise ValueError('NGK runtime version differs')
    options=rosetta.basic.options
    for kind,values in DEFAULT_CHECKS.items():
        getter=getattr(options,'get_'+kind+'_option')
        for key,expected in values.items():
            if getter(key)!=expected:raise ValueError('Nondefault NGK option: '+key)
    for kind,values in [('boolean',BOOLEAN_OPTIONS),('integer',INTEGER_OPTIONS),('string',STRING_OPTIONS)]:
        setter=getattr(options,'set_'+kind+'_option');getter=getattr(options,'get_'+kind+'_option')
        for key,value in values.items():
            setter(key,value)
            if getter(key)!=value:raise ValueError('NGK option setter failed: '+key)
    return dict(parameter_sha256=parameter_sha256(),parameters=copy.deepcopy(PARAMETERS))


def make_loops(rosetta, definitions):
    loops=rosetta.protocols.loops.Loops()
    for x in definitions:
        loops.add_loop(rosetta.protocols.loops.Loop(x['start'],x['stop'],x['cut'],x['skip'],x['extended']))
    return loops


def make_mover(rosetta, definitions):
    mover=rosetta.protocols.relax.loop.LoopRelaxMover()  # initializes native score functions
    mover.loops(make_loops(rosetta,definitions))
    if (mover.remodel(),mover.refine(),mover.intermedrelax(),mover.relax()) != ('perturb_kic','refine_kic','no','no'):
        raise ValueError('Native whole-protocol stages differ')
    # No native/reference target, task factory, MoveMap, manual KIC, minimize,
    # relax, cycles shortening, or best-of selection is injected here.
    return mover


def inspect_runtime(rosetta):
    result=configure_runtime(rosetta,copy.deepcopy(PARAMETERS))
    mover=make_mover(rosetta,[dict(start=3,stop=10,cut=10,skip=0.,extended=True),
                                 dict(start=20,stop=27,cut=27,skip=0.,extended=True)])
    result.update(native_class=type(mover).__name__,n_rebuild_tries=mover.n_rebuild_tries(),
        fa_score_name=rosetta.protocols.loops.get_fa_scorefxn().get_name(),
        cen_score_name=rosetta.protocols.loops.get_cen_scorefxn().get_name(),
        dual_loop_object_constructed=True,pose_loads=0,native_apply_calls=0)
    return result


def chemical_topology(rosetta,pose):
    adjacent=[]
    for i in range(1,pose.size()):
        a,b=pose.residue(i),pose.residue(i+1)
        if a.has('C') and b.has('N'):
            adjacent.append([i,i+1,bool(pose.conformation().is_bonded(
                rosetta.core.id.AtomID(a.atom_index('C'),i),
                rosetta.core.id.AtomID(b.atom_index('N'),i+1)))])
    return dict(sequence=pose.sequence(),chains=[pose.chain(i) for i in range(1,pose.size()+1)],
        termini=[[i,bool(pose.residue(i).is_lower_terminus()),bool(pose.residue(i).is_upper_terminus())]
                 for i in range(1,pose.size()+1)],adjacent_CN_bonds=adjacent)


def foldtree_compatibility(rosetta,pose,definitions,before):
    # Construct the exact tree the native entry would use, without assigning it
    # or changing coordinates/bonds. Never repair the native protocol's tree.
    native_tree=rosetta.core.kinematics.FoldTree()
    rosetta.protocols.loops.fold_tree_from_loops(pose,make_loops(rosetta,definitions),native_tree,True)
    real_gaps=[i for i,j,bonded in before['adjacent_CN_bonds'] if not bonded]
    unsupported=[i for i in real_gaps if not native_tree.is_cutpoint(i)]
    return dict(compatible=not unsupported,real_nonbonded_boundaries=real_gaps,
        native_tree_missing_gap_cutpoints=unsupported,native_fold_tree=str(native_tree))


def execute(pose,row,params,emit):
    import pyrosetta
    rosetta=pyrosetta.rosetta
    definitions=loop_definitions(row)
    runtime=configure_runtime(rosetta,params)
    for x in definitions:
        if not (1<x['start'] and x['stop']<pose.size()):raise ValueError('NGK requires two loop anchors')
        if len({pose.chain(i) for i in range(x['start']-1,x['stop']+2)})!=1:
            raise ValueError('NGK loop crosses a real chain boundary')
    topology_before=chemical_topology(rosetta,pose)
    compatibility=foldtree_compatibility(rosetta,pose,definitions,topology_before)
    if not compatibility['compatible']:
        report=dict(status='NOT_APPLICABLE',reason='native_default_foldtree_bridges_source_gap',
            native_apply_calls=0,source_topology=topology_before,foldtree_compatibility=compatibility,
            work_budget=work_budget(row),runtime=runtime)
        emit(dict(event='ngk_not_applicable',**report),pose)
        return None,report
    mover=make_mover(rosetta,definitions)
    emit(dict(event='ngk_native_start',loop_definitions=definitions,
              work_budget=work_budget(row),runtime=runtime),pose)
    wall=time.monotonic();cpu=time.process_time()
    error=None
    try:
        mover.apply(pose)  # exactly one native full trajectory, internal flow intact
    except Exception as exc:
        error=dict(type=type(exc).__name__,message=str(exc))
    status=mover.get_last_move_status()
    topology_after=chemical_topology(rosetta,pose)
    topology_preserved=topology_after==topology_before
    report=dict(status='COMPLETED' if error is None and status==rosetta.protocols.moves.MS_SUCCESS and topology_preserved else 'NATIVE_FAILED',
        error=error,
        native_move_status=str(status),native_apply_calls=1,
        wall_seconds=time.monotonic()-wall,process_cpu_seconds=time.process_time()-cpu,
        work_budget=work_budget(row),runtime=runtime,loop_definitions=definitions,
        output_selection='unmodified_native_protocol_return',reference_used_for_generation=False,
        source_topology_preserved=topology_preserved,source_topology_before=topology_before,
        source_topology_after=topology_after,foldtree_compatibility=compatibility)
    emit(dict(event='ngk_native_terminal',**report),pose)
    return pose,report
