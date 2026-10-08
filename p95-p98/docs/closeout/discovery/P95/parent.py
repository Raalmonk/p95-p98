def decide(view):
    # One unevaluated candidate: completed-startup polish and Pareto-qualified
    # accepted-state resolution, preserving independent-record MC patience.
    # Same-binding e9 gains both energies over current but loses both RMSDs
    # and efficiency. Peer 561 gains four axes but narrowly loses local RMSD.
    # Peers 551/de9/633 gain energies and efficiency at costs to both RMSDs.
    # These component-balanced tradeoffs do not isolate individual mechanisms.
    # Paired WS effects versus matched NGK favor RMSDs, not energies; hard
    # gains local energy but loses global energy and RMSDs on 15/16 valid pairs.
    # Fixed-router and native-ProMod3 quality deltas favor current on their
    # reported both-valid subsets. RAW/MIN1 remain historical references.
    # Current and peers report 48/48 VALID, complete MP and no timeouts.
    # Full paired row/component tables and retention-quality scores are absent.
    # Both startup examples decrease energies under native acceptance but lack
    # matched offline quality; the database child and new continuations are unscored.
    # Direct-parent availability conflicts between card and log; native_seed
    # is unavailable. TRAIN48 has 32 components and incomplete routing coverage.
    # No evaluator is exposed: evaluate this single candidate on all TRAIN48
    # and assimilate all five objectives before another proposal wave.
    # Preserve live qualifications, charged preparation/specialist reuse,
    # cumulative allowances and native-low delivery. CPU, logical work,
    # waiting and offline scoring remain separate; hardware speed is not a gain.
    # Source geometry and displacement never certify reference accuracy.
    event = view['event']
    observation = view['observation']
    memory = view['memory']

    if event == 'route':
        states = observation['states']
        raw = states[0]
        for state in states:
            if state['slot'] == 0:
                raw = state

        if 'routing' not in memory:
            memory['routing'] = {
                'initial_remaining': observation['remaining_work'],
                'attempts': [],
                'startup_only': False
            }
        routing = memory['routing']
        attempts = routing['attempts']
        raw_valid = raw['source']['geometry_valid'] is True

        # Retained states retain their own diagnostics. RAW remains eligible.
        best = raw
        for state in states:
            a = state['source']
            b = best['source']
            av = a['geometry_valid'] is True
            bv = b['geometry_valid'] is True
            choose = av and not bv
            if av and bv:
                ag = a['fixed_global_energy']
                al = a['fixed_local_energy']
                bg = b['fixed_global_energy']
                bl = b['fixed_local_energy']
                if ag is not None and al is not None and bg is not None and bl is not None:
                    # Preserve the incumbent on an energy tradeoff.
                    choose = ag <= bg and al <= bl and (ag < bg or al < bl)
            elif not av and not bv:
                au = 0
                bu = 0
                ae = 0.0
                be = 0.0
                for field in ['cn_exceedance', 'bond_exceedance',
                              'extreme_exceedance', 'contact_exceedance']:
                    if field not in a or a[field] is None:
                        au += 1
                    else:
                        ae += max(0.0, a[field])
                    if field not in b or b[field] is None:
                        bu += 1
                    else:
                        be += max(0.0, b[field])
                choose = (a['geometry_valid'] is None, au, ae) < (
                    b['geometry_valid'] is None, bu, be)
            if choose:
                best = state

        parent = best['slot']
        keep = [0]
        if parent != 0:
            keep = keep + [parent]
        for state in states:
            if state['slot'] not in keep and len(keep) < 9:
                keep = keep + [state['slot']]

        action = 'deliver'
        names = []
        if len(attempts) == 0:
            if raw_valid:
                source = raw['source']
                gentle = True
                if source['fixed_local_energy'] is None or source['fixed_local_energy'] > 0.0:
                    gentle = False

                # Require measured loop and residue evidence. An aggregate
                # favorable energy must not conceal a highly strained residue.
                if 'per_loop' not in source or source['per_loop'] is None:
                    gentle = False
                else:
                    if len(source['per_loop']) == 0:
                        gentle = False
                    for loop in source['per_loop']:
                        if 'fixed_energy' not in loop or loop['fixed_energy'] is None:
                            gentle = False
                        elif loop['fixed_energy'] > 0.0:
                            gentle = False

                if 'per_residue' not in source or source['per_residue'] is None:
                    gentle = False
                else:
                    if len(source['per_residue']) == 0:
                        gentle = False
                    for residue in source['per_residue']:
                        if 'missing' not in residue or residue['missing'] is not False:
                            gentle = False
                        if 'fixed_energy' not in residue or residue['fixed_energy'] is None:
                            gentle = False
                        elif residue['fixed_energy'] > 5.0:
                            gentle = False

                # Transfer bounded startup to fully gentle neighborhoods too.
                # Require complete movable-loop evidence; favorable aggregate
                # energy cannot substitute for missing measurements.
                routing['startup_only'] = False
                if 'loop_intervals' in source and source['loop_intervals'] is not None:
                    movable_ok = (
                        source['fixed_local_energy'] is not None
                        and source['fixed_global_energy'] is not None
                    )
                    intervals = []
                    if 'loop_intervals' in source and source['loop_intervals'] is not None:
                        intervals = source['loop_intervals']
                    if len(intervals) == 0:
                        movable_ok = False

                    loop_ids = []
                    if 'per_loop' not in source or source['per_loop'] is None:
                        movable_ok = False
                    else:
                        if len(source['per_loop']) != len(intervals):
                            movable_ok = False
                        for loop in source['per_loop']:
                            if 'loop_index' not in loop or loop['loop_index'] is None:
                                movable_ok = False
                            else:
                                index = loop['loop_index']
                                if index < 0 or index >= len(intervals) or index in loop_ids:
                                    movable_ok = False
                                else:
                                    loop_ids = loop_ids + [index]
                            if 'fixed_energy' not in loop or loop['fixed_energy'] is None:
                                movable_ok = False
                            elif loop['fixed_energy'] > 0.0:
                                movable_ok = False
                    if len(loop_ids) != len(intervals):
                        movable_ok = False

                    seen = []
                    if 'per_residue' not in source or source['per_residue'] is None:
                        movable_ok = False
                    else:
                        if len(source['per_residue']) == 0:
                            movable_ok = False
                        for residue in source['per_residue']:
                            movable = False
                            if 'index' not in residue or residue['index'] is None:
                                movable_ok = False
                            else:
                                for interval in intervals:
                                    if interval[0] <= residue['index'] <= interval[1]:
                                        movable = True
                                if movable:
                                    if residue['index'] in seen:
                                        movable_ok = False
                                    else:
                                        seen = seen + [residue['index']]
                            if 'missing' not in residue or residue['missing'] is not False:
                                movable_ok = False
                            if 'fixed_energy' not in residue or residue['fixed_energy'] is None:
                                movable_ok = False
                            elif movable and residue['fixed_energy'] > 5.0:
                                movable_ok = False

                    for interval in intervals:
                        expected = interval[1] - interval[0] + 1
                        observed = sum([
                            1 for index in seen
                            if interval[0] <= index <= interval[1]
                        ])
                        if expected <= 0 or observed != expected:
                            movable_ok = False
                    routing['startup_only'] = movable_ok

                # Complete low-strain loops receive native startup without
                # backbone exploration, then one qualified descent. Capability
                # availability and cumulative affordability remain authoritative.
                if gentle and not routing['startup_only']:
                    names = ['minimize', 'ngk_refine']
                else:
                    names = ['ngk_refine', 'minimize']
            else:
                names = ['promod3_database', 'ngk_rebuild',
                         'ngk_refine', 'minimize']
        elif best['source']['geometry_valid'] is not True and len(attempts) < 3:
            names = ['promod3_database', 'ngk_rebuild',
                     'ngk_refine', 'minimize']
        elif raw_valid and len(attempts) == 1 and attempts[0] == 'minimize':
            # RAW remains incumbent unless a valid child improves both energy
            # axes weakly and at least one strictly. A failed or unhelpful probe
            # may escalate once, from RAW, within the original allowance.
            if best['slot'] == 0:
                names = ['ngk_refine']
        elif raw_valid and len(attempts) < 3 and 'ngk_refine' in attempts and 'minimize' not in attempts and (
            routing['startup_only'] or (
                'ngk_control' in memory
                and 'startup_resolved' in memory['ngk_control']
                and memory['ngk_control']['startup_resolved']
            )
        ):
            # Startup and minimization are different interventions: an
            # unhelpful startup does not establish that descent is exhausted.
            # Test the energy-oriented peer's polish mechanism, but require
            # a completed startup with an actually retained, measured valid
            # output. An attempted action or startup flag alone is insufficient.
            # Polish the delivery incumbent, possibly RAW, not an unqualified
            # child. Existing live parent, capacity and budget checks apply.
            source = best['source']
            polish = (
                source['geometry_valid'] is True
                and source['fixed_global_energy'] is not None
                and source['fixed_local_energy'] is not None
                and observation['remaining_work'] > 24.0
            )
            if polish and routing['startup_only']:
                polish = False
                history = observation['history']
                if history is not None and len(history) > 0:
                    last = history[-1]
                    completed = (
                        'action' in last and last['action'] is not None
                        and last['action'][:11] == 'ngk_refine:'
                        and 'outcome' in last and last['outcome'] == 'COMPLETED'
                        and 'parent_slot' in last and last['parent_slot'] == 0
                        and 'result_slots' in last
                        and last['result_slots'] is not None
                    )
                    if completed:
                        for state in states:
                            if state['slot'] != 0 and state['slot'] in last['result_slots']:
                                child = state['source']
                                if (
                                    child['geometry_valid'] is True
                                    and child['fixed_global_energy'] is not None
                                    and child['fixed_local_energy'] is not None
                                ):
                                    polish = True
            if polish:
                names = ['minimize']
        elif len(attempts) < 3 and 'minimize' not in attempts:
            # Transfer the measured peer's single retained-child polish.
            # RAW fallback is narrower: unfavorable flank energy alone does
            # not establish strain inside the movable region. This gate is
            # an unmeasured hypothesis, not a counterfactual quality label.
            source = best['source']
            strained = False
            if source['geometry_valid'] is True and source['fixed_global_energy'] is not None and source['fixed_local_energy'] is not None:
                strained = best['slot'] != 0 and source['fixed_local_energy'] > 0.0
                if 'per_loop' in source and source['per_loop'] is not None:
                    for loop in source['per_loop']:
                        if 'fixed_energy' in loop and loop['fixed_energy'] is not None:
                            if loop['fixed_energy'] > 0.0:
                                strained = True
                if 'per_residue' in source and source['per_residue'] is not None:
                    for residue in source['per_residue']:
                        eligible_residue = best['slot'] != 0
                        if not eligible_residue:
                            if 'index' in residue and residue['index'] is not None:
                                if 'loop_intervals' in source and source['loop_intervals'] is not None:
                                    for interval in source['loop_intervals']:
                                        if interval[0] <= residue['index'] <= interval[1]:
                                            eligible_residue = True
                        if eligible_residue:
                            if 'missing' in residue and residue['missing'] is False:
                                if 'fixed_energy' in residue and residue['fixed_energy'] is not None:
                                    if residue['fixed_energy'] > 5.0:
                                        strained = True
            # A repaired incumbent can merit one polish even with negative
            # energies. Compare actual retained endpoints, not independent minima.
            # Preserve the existing valid-source displacement restriction.
            # For initially invalid geometry, necessary repair displacement
            # must not permanently exclude subsequent qualified minimization.
            progress_polish = False
            if not strained and best['slot'] != 0 and (
                'ngk_refine' in attempts or 'ngk_rebuild' in attempts
                or 'promod3_database' in attempts
            ):
                baseline = raw['source']
                comparable = (
                    source['geometry_valid'] is True
                    and source['fixed_global_energy'] is not None
                    and source['fixed_local_energy'] is not None
                    and baseline['fixed_global_energy'] is not None
                    and baseline['fixed_local_energy'] is not None
                    and 'per_loop' in baseline and baseline['per_loop'] is not None
                    and 'per_loop' in source and source['per_loop'] is not None
                    and 'loop_intervals' in baseline
                    and baseline['loop_intervals'] is not None
                )
                if comparable:
                    # Transfer the peer's material-gain gate without assuming
                    # its measured whole-program effects isolate this mechanism.
                    # Neither energy may regress; all existing loop coverage,
                    # geometry, displacement and live capability checks remain.
                    progress_polish = (
                        source['fixed_global_energy'] <= baseline['fixed_global_energy']
                        and source['fixed_local_energy'] <= baseline['fixed_local_energy']
                        and (
                            source['fixed_global_energy'] < baseline['fixed_global_energy'] - 0.5
                            or source['fixed_local_energy'] < baseline['fixed_local_energy'] - 0.25
                        )
                    )
                    before_loops = {
                        loop['loop_index']: loop['fixed_energy']
                        for loop in baseline['per_loop']
                        if 'loop_index' in loop and loop['loop_index'] is not None
                        and 'fixed_energy' in loop and loop['fixed_energy'] is not None
                    }
                    after_loops = {
                        loop['loop_index']: loop['fixed_energy']
                        for loop in source['per_loop']
                        if 'loop_index' in loop and loop['loop_index'] is not None
                        and 'fixed_energy' in loop and loop['fixed_energy'] is not None
                    }
                    loop_count = len(baseline['loop_intervals'])
                    complete = (
                        0 < loop_count <= 64
                        and len(before_loops) == loop_count
                        and len(after_loops) == loop_count
                        and len(baseline['per_loop']) == loop_count
                        and len(source['per_loop']) == loop_count
                    )
                    if complete:
                        for index in range(loop_count):
                            if index not in before_loops or index not in after_loops:
                                complete = False
                            elif after_loops[index] > before_loops[index]:
                                progress_polish = False
                        for loop in source['per_loop']:
                            if 'source_displacement_A' not in loop or loop['source_displacement_A'] is None:
                                complete = False
                            elif loop['source_displacement_A'] < 0:
                                complete = False
                            elif raw_valid and loop['source_displacement_A'] > 0.5:
                                complete = False
                    # Geometry qualification and paired energy progress are
                    # required; neither certifies reference accuracy. Unknown
                    # displacement remains unknown, including after rebuilding.
                    progress_polish = progress_polish and complete
            if (strained or progress_polish) and observation['remaining_work'] > 24.0:
                # The existing live capability/price checks remain mandatory.
                # RAW and the delivery incumbent stay retained during polish.
                names = ['minimize']

        left = observation['remaining_work']
        origin = routing['initial_remaining']

        # One additional descent only after an inexpensive completed descent
        # produced the incumbent. Historical cost is not a future work price.
        repeat_descent = False
        descent_count = sum([1 for name in attempts if name == 'minimize'])
        if len(names) == 0 and raw_valid and best['slot'] != 0:
            if 0 < len(attempts) < 3 and attempts[-1] == 'minimize' and descent_count == 1:
                history = observation['history']
                if history is not None and len(history) > 0 and left > 24.0:
                    last = history[-1]
                    completed = (
                        'action' in last and last['action'] is not None
                        and last['action'][:9] == 'minimize:'
                        and 'outcome' in last and last['outcome'] == 'COMPLETED'
                        and 'result_slots' in last and last['result_slots'] is not None
                        and best['slot'] in last['result_slots']
                        and 'parent_slot' in last
                        and 'work' in last and last['work'] is not None
                    )
                    if completed:
                        inexpensive = (
                            0 <= last['work'] <= 0.02 * origin
                            and 0 <= origin - left <= 0.05 * origin
                        )
                        previous = None
                        for state in states:
                            if state['slot'] == last['parent_slot']:
                                previous = state
                        if inexpensive and previous is not None:
                            before = previous['source']
                            after = best['source']
                            progressing = (
                                before['geometry_valid'] is True
                                and after['geometry_valid'] is True
                                and before['fixed_global_energy'] is not None
                                and before['fixed_local_energy'] is not None
                                and after['fixed_global_energy'] is not None
                                and after['fixed_local_energy'] is not None
                            )
                            if progressing:
                                # Compare the actual descent parent and child.
                                # One material gain suffices without regression;
                                # residual movable strain must still justify
                                # this bounded second and final descent.
                                progressing = (
                                    after['fixed_global_energy'] <= before['fixed_global_energy']
                                    and after['fixed_local_energy'] <= before['fixed_local_energy']
                                    and (
                                        after['fixed_global_energy'] < before['fixed_global_energy'] - 0.5
                                        or after['fixed_local_energy'] < before['fixed_local_energy'] - 0.25
                                    )
                                )
                            measured = (
                                'per_loop' in before and before['per_loop'] is not None
                                and 'per_loop' in after and after['per_loop'] is not None
                                and 'loop_intervals' in raw['source']
                                and raw['source']['loop_intervals'] is not None
                            )
                            if measured:
                                before_loops = {
                                    loop['loop_index']: loop['fixed_energy']
                                    for loop in before['per_loop']
                                    if 'loop_index' in loop and loop['loop_index'] is not None
                                    and 'fixed_energy' in loop and loop['fixed_energy'] is not None
                                }
                                after_loops = {
                                    loop['loop_index']: loop['fixed_energy']
                                    for loop in after['per_loop']
                                    if 'loop_index' in loop and loop['loop_index'] is not None
                                    and 'fixed_energy' in loop and loop['fixed_energy'] is not None
                                }
                                loop_count = len(raw['source']['loop_intervals'])
                                measured = (
                                    loop_count > 0
                                    and len(before_loops) == loop_count
                                    and len(after_loops) == loop_count
                                    and len(before['per_loop']) == loop_count
                                    and len(after['per_loop']) == loop_count
                                )
                                for index in range(loop_count):
                                    if index not in before_loops or index not in after_loops:
                                        measured = False
                                    elif after_loops[index] > before_loops[index]:
                                        progressing = False
                                for loop in after['per_loop']:
                                    # Absolute child displacement bounds intervention;
                                    # it is neither a pairwise distance nor target RMSD.
                                    if 'source_displacement_A' not in loop or loop['source_displacement_A'] is None:
                                        measured = False
                                    elif not 0 <= loop['source_displacement_A'] <= 0.5:
                                        measured = False
                            if progressing and measured:
                                # Require a measured remaining reason for the
                                # second descent, not just a large first gain.
                                # Inspect actual movable-loop strain rather than
                                # favorable flanks or independent energy minima.
                                residual_strain = False
                                for loop in after['per_loop']:
                                    if loop['fixed_energy'] > 0.0:
                                        residual_strain = True
                                if 'per_residue' in after and after['per_residue'] is not None:
                                    for residue in after['per_residue']:
                                        observed = (
                                            'index' in residue and residue['index'] is not None
                                            and 'missing' in residue and residue['missing'] is False
                                            and 'fixed_energy' in residue
                                            and residue['fixed_energy'] is not None
                                        )
                                        if observed and residue['fixed_energy'] > 5.0:
                                            for interval in raw['source']['loop_intervals']:
                                                if interval[0] <= residue['index'] <= interval[1]:
                                                    residual_strain = True
                                # Missing strain evidence does not certify good
                                # geometry or accuracy; it simply does not fund
                                # this additional discretionary intervention.
                                if residual_strain:
                                    repeat_descent = True
                                    names = ['minimize']

        ngk_used = 'ngk_refine' in attempts or 'ngk_rebuild' in attempts

        # Absolute remaining-work floor, anchored once after preparation.
        # Prior actions and backend prefixes never reset this allowance.
        cutoff = max(24.0, origin * (0.75 if raw_valid else 0.15))

        for name in names:
            # Only minimization may use a retained child. Database and MC
            # retain the host's qualified frozen RAW-derived preparation.
            selected_parent = 0
            if name == 'minimize' and best['source']['geometry_valid'] is True:
                selected_parent = best['slot']
            is_ngk = name in ['ngk_refine', 'ngk_rebuild']
            eligible = name not in attempts or (name == 'minimize' and repeat_descent)
            if is_ngk and (ngk_used or left <= cutoff):
                eligible = False
            if eligible:
                for cap in observation['available_actions']:
                    if cap['name'] == name and selected_parent in cap['parent_slots']:
                        required = [0]
                        if best['slot'] != 0:
                            required = required + [best['slot']]
                        capacity = 9 - cap['max_outputs']
                        price = cap['maximum_work']
                        # Only current parent-specific qualifications apply.
                        # The host separately enforces cumulative CPU/wall,
                        # chemistry, frozen preparation charges and delivery.
                        if price is not None and 0 <= price <= left and len(required) <= capacity:
                            action = cap['token']
                            parent = selected_parent
                            keep = required
                            for state in states:
                                if state['slot'] not in keep and len(keep) < capacity:
                                    keep = keep + [state['slot']]
                            routing['attempts'] = attempts + [name]
                            if is_ngk:
                                memory['ngk_control'] = {
                                    'cutoff': cutoff,
                                    'origin': origin,
                                    'repair': not raw_valid,
                                    'startup_only': (
                                        raw_valid and routing['startup_only']
                                        and name == 'ngk_refine'
                                    ),
                                    'startup_done': False,
                                    'startup_before': None,
                                    'startup_checked': False,
                                    'resolution_epoch': None,
                                    'resolution_left': None,
                                    'startup_resolved': False,
                                    'epoch': None,
                                    'low_global': None,
                                    'low_local': None,
                                    'progress_left': None
                                }
                            break
            if action != 'deliver':
                break

        decision = {'action': action, 'parent_slot': parent, 'keep_slots': keep}

    elif event == 'pre_proposal':
        decision = {'stop': False, 'restore_slot': None, 'loop_index': None,
                    'perturbation': 'native', 'repack': 'native', 'minimize': 'native'}
        if 'ngk_control' in memory:
            control = memory['ngk_control']
            left = observation['remaining_work']
            # Stop alone after native startup acceptance, or before the first
            # loop choice if it occurs earlier. Never request a new operation
            # merely to complete startup, and never renew the original budget.
            if control['startup_only'] and (
                control['startup_done'] or observation['site'] == 'choose_loop'
            ):
                decision['stop'] = True
            elif left is not None:
                if left <= control['cutoff']:
                    decision['stop'] = True
                elif observation['site'] == 'choose_loop' and not control['repair']:
                    # Missing accepted-state evidence cannot renew patience.
                    # Never substitute a potentially rejected working proposal.
                    # The cumulative cutoff above remains independently active.
                    state = observation['accepted_current']
                    if state is not None and len(state['loop_energies']) > 0:
                        global_energy = state['fixed']['total']
                        local_energy = sum([
                            loop['fixed_energy'] for loop in state['loop_energies']
                        ])
                        epoch = observation['score_epoch']
                        control['epoch'] = epoch
                        # Fixed evaluation weights remain comparable across
                        # native score epochs. A schedule change alone is not
                        # progress and must not restart the stagnation clock.
                        if control['low_global'] is None:
                            control['low_global'] = global_energy
                            control['low_local'] = local_energy
                            control['progress_global'] = global_energy
                            control['global_witness_local'] = local_energy
                            control['global_witness_visit'] = observation['step']
                            control['progress_local'] = local_energy
                            control['local_witness_global'] = global_energy
                            control['local_witness_visit'] = observation['step']
                            control['progress_left'] = left
                        else:
                            # Transfer independent material-record patience from
                            # the matched RMSD-oriented peers. A useful energy
                            # tradeoff need not improve the other axis relative
                            # to an old witness. Each record still belongs to
                            # an actual accepted visit, with its own diagnostics.
                            # Records are not an archive or simultaneous gains.
                            # Their own-axis thresholds decrease monotonically;
                            # revisiting an old tradeoff cannot renew patience.
                            # The original cutoff and stagnation limits remain.
                            control['low_global'] = min(control['low_global'], global_energy)
                            control['low_local'] = min(control['low_local'], local_energy)
                            global_progress = (
                                global_energy < control['progress_global'] - 0.5
                            )
                            local_progress = (
                                local_energy < control['progress_local'] - 0.25
                            )
                            if global_progress:
                                control['progress_global'] = global_energy
                                control['global_witness_local'] = local_energy
                                control['global_witness_visit'] = observation['step']
                            if local_progress:
                                control['progress_local'] = local_energy
                                control['local_witness_global'] = global_energy
                                control['local_witness_visit'] = observation['step']
                            if global_progress or local_progress:
                                # Diagnostic witnesses are not archived states.
                                # No restore, score-epoch reset, RNG rewind or
                                # renewal of the original resource allowance.
                                control['progress_left'] = left

                            history = observation['history']
                            spent = control['origin'] - left
                            stalled = control['progress_left'] - left
                            # Separate progress traces, not a synthetic state
                            # combining minima from different visits.
                            if history is not None and len(history) >= 16:
                                if spent >= 0.10 * control['origin'] and stalled >= max(48.0, 0.06 * control['origin']):
                                    decision['stop'] = True

            # Reassess at epoch boundaries and after bounded work intervals.
            # Resolution within an epoch need not wait for a weight change.
            # Reuse only the supplied accepted-state observation; request no
            # additional scoring. Every existing completeness, paired-energy,
            # connection and displacement gate below still applies.
            # This diagnostic clock never renews patience or any allowance.
            # Existing stop protections take priority.
            if not decision['stop'] and not control['repair'] and not control['startup_only']:
                if observation['site'] == 'choose_loop' and (
                    not control['startup_checked'] or (
                        observation['score_epoch'] is not None
                        and observation['score_epoch'] != control['resolution_epoch']
                    ) or (
                        left is not None
                        and control['resolution_left'] is not None
                        and control['resolution_left'] - left >= max(8.0, 0.01 * control['origin'])
                    )
                ):
                    control['startup_checked'] = True
                    control['resolution_epoch'] = observation['score_epoch']
                    control['resolution_left'] = left
                    # Never substitute a potentially rejected working proposal.
                    # Missing accepted-state evidence leaves ordinary MC intact.
                    state = observation['accepted_current']
                    before = control['startup_before']
                    intervals = observation['loop_intervals_zero_based']
                    ready = (
                        control['startup_done']
                        and state is not None and before is not None
                        and 0 < len(intervals) <= 64
                    )
                    after = {}
                    if ready:
                        ready = len(state['loop_energies']) == len(intervals)
                        for loop in state['loop_energies']:
                            index = loop['loop_index']
                            key = str(index)
                            value = loop['fixed_energy']
                            if not 0 <= index < len(intervals) or key in after or value is None:
                                ready = False
                            else:
                                after[key] = value
                                if key not in before['loops']:
                                    ready = False
                                elif value > 0.0 or value > before['loops'][key]:
                                    ready = False
                        if len(after) != len(intervals):
                            ready = False

                    # Compare two actual accepted visits under fixed weights.
                    # Require no regression on either energy, but material
                    # progress on either one suffices. Do not spend additional
                    # MC work solely to cross both materiality thresholds.
                    # All subsequent coverage, connection, displacement and
                    # residue-strain gates remain mandatory. This is a stopping
                    # hypothesis, not evidence of reference-quality improvement.
                    if ready:
                        global_energy = state['fixed']['total']
                        if global_energy is None:
                            ready = False
                        else:
                            local_energy = sum([after[key] for key in after])
                            before_local = sum([
                                before['loops'][key] for key in before['loops']
                            ])
                            ready = (
                                global_energy <= before['global']
                                and local_energy <= before_local
                                and (
                                    global_energy < before['global'] - 0.5
                                    or local_energy < before_local - 0.25
                                )
                            )

                    if ready:
                        source = state['source']
                        loop_ids = []
                        if len(source['loops']) != len(intervals):
                            ready = False
                        for loop in source['loops']:
                            index = loop['loop_index']
                            if not 0 <= index < len(intervals) or index in loop_ids:
                                ready = False
                            else:
                                loop_ids = loop_ids + [index]
                                start = intervals[index][0]
                                end = intervals[index][1]
                                expected = end - start + 1
                                if expected <= 0 or loop['start'] != start or loop['end'] != end:
                                    ready = False

                                displacement = loop['ca_displacement_max_A']
                                if not displacement['available'] or displacement['value'] is None:
                                    ready = False
                                elif not 0 <= displacement['value'] <= 0.5:
                                    ready = False
                                if loop['ca_displacement_missing_count'] != 0 or loop['ca_displacement_observed_count'] != expected:
                                    ready = False

                                # Every applicable internal/seam connection
                                # must be observed, present and within bounds.
                                edges = []
                                first_edge = max(0, start - 1)
                                last_edge = min(source['sequence_length'] - 2, end)
                                for connection in loop['connections']:
                                    pair = connection['residues']
                                    if len(pair) != 2:
                                        ready = False
                                    elif pair[1] != pair[0] + 1 or not first_edge <= pair[0] <= last_edge or pair[0] in edges:
                                        ready = False
                                    else:
                                        edges = edges + [pair[0]]
                                    distance = connection['distance_A']
                                    if connection['missing_c'] or connection['missing_n'] or not connection['polymer_edge_present']:
                                        ready = False
                                    if not distance['available'] or distance['value'] is None:
                                        ready = False
                                    elif not 1.2 <= distance['value'] <= 1.5:
                                        ready = False
                                if len(edges) != max(0, last_edge - first_edge + 1):
                                    ready = False
                        if len(loop_ids) != len(intervals):
                            ready = False

                    if ready:
                        seen = {}
                        for residue in source['residues']:
                            index = residue['index']
                            movable = False
                            for interval in intervals:
                                if interval[0] <= index <= interval[1]:
                                    movable = True
                            if movable:
                                key = str(index)
                                if key in seen:
                                    ready = False
                                seen[key] = index
                                if residue['backbone_missing_count'] != 0 or not residue['in_loop']:
                                    ready = False
                                energy = residue['fixed_weighted_residue_energy']
                                if energy is None or energy > 5.0:
                                    ready = False
                            elif residue['in_loop']:
                                ready = False
                        for interval in intervals:
                            observed = sum([
                                1 for key in seen
                                if interval[0] <= seen[key] <= interval[1]
                            ])
                            if observed != interval[1] - interval[0] + 1:
                                ready = False

                    if ready:
                        # Stop alone. Native-low delivery and outer endpoint
                        # qualification remain unchanged; no RNG/budget rewind.
                        control['startup_resolved'] = True
                        decision['stop'] = True

    elif event == 'accept':
        decision = {'mode': 'native', 'probability': None, 'temperature_multiplier': None}
        if 'ngk_control' in memory:
            control = memory['ngk_control']
            if observation['site'] == 'initial_repack':
                # This precedes native acceptance. Store the previous-current
                # baseline, never assume candidate acceptance or improvement.
                control['startup_done'] = True
                if not control['repair'] and not control['startup_only']:
                    current = observation['accepted_current']
                    intervals = observation['loop_intervals_zero_based']
                    control['startup_before'] = None
                    if current is not None and 0 < len(intervals) <= 64:
                        values = {}
                        complete = (
                            len(current['loop_energies']) == len(intervals)
                            and current['fixed']['total'] is not None
                        )
                        for loop in current['loop_energies']:
                            index = loop['loop_index']
                            key = str(index)
                            value = loop['fixed_energy']
                            if not 0 <= index < len(intervals) or key in values or value is None:
                                complete = False
                            else:
                                values[key] = value
                        if complete and len(values) == len(intervals):
                            # Bounded diagnostic memory, not an archive state.
                            control['startup_before'] = {
                                'observed_step': observation['step'],
                                'global': current['fixed']['total'],
                                'loops': values
                            }
        if 'ngk_control' in memory and not memory['ngk_control']['repair'] and not memory['ngk_control']['startup_only']:
            delta = observation['working_minus_current']
            current = observation['accepted_current']
            candidate = observation['working_state']
            active_delta = observation['energy_delta']
            if delta is not None and current is not None and candidate is not None:
                displacement = delta['loop_ca_displacement']
                mean = displacement['mean_A']
                if active_delta is not None and active_delta > 0 and delta['fixed_energy'] > 0:
                    if displacement['missing_count'] == 0 and displacement['observed_count'] > 0 and mean is not None and mean > 0.5:
                        if len(current['loop_energies']) > 0 and len(candidate['loop_energies']) == len(current['loop_energies']):
                            # Match loop identities: a summed increase can hide
                            # improvement in another loop. Mixed or unmeasured
                            # tradeoffs retain native acceptance.
                            before = {
                                loop['loop_index']: loop['fixed_energy']
                                for loop in current['loop_energies']
                            }
                            after = {
                                loop['loop_index']: loop['fixed_energy']
                                for loop in candidate['loop_energies']
                            }
                            comparable = (
                                len(before) == len(current['loop_energies'])
                                and len(after) == len(candidate['loop_energies'])
                                and len(before) == len(after)
                            )
                            improved = False
                            worsened = False
                            for loop_index in before:
                                if loop_index not in after:
                                    comparable = False
                                elif before[loop_index] is None or after[loop_index] is None:
                                    comparable = False
                                else:
                                    if after[loop_index] < before[loop_index]:
                                        improved = True
                                    if after[loop_index] > before[loop_index]:
                                        worsened = True
                            if comparable and worsened and not improved:
                                # Energy-based cooling must not obstruct recovery
                                # from a transient connection defect. Require
                                # complete, intact local C-N connections in both
                                # actual states; otherwise retain native acceptance.
                                # This is not a full chemistry or accuracy certificate.
                                intervals = observation['loop_intervals_zero_based']
                                closed = 0 < len(intervals) <= 64
                                if closed:
                                    for checked_state in [current, candidate]:
                                        source = checked_state['source']
                                        loop_ids = []
                                        if len(source['loops']) != len(intervals):
                                            closed = False
                                        for loop in source['loops']:
                                            index = loop['loop_index']
                                            if not 0 <= index < len(intervals) or index in loop_ids:
                                                closed = False
                                            else:
                                                loop_ids = loop_ids + [index]
                                                start = intervals[index][0]
                                                end = intervals[index][1]
                                                if end < start or loop['start'] != start or loop['end'] != end:
                                                    closed = False
                                                first_edge = max(0, start - 1)
                                                last_edge = min(source['sequence_length'] - 2, end)
                                                edges = []
                                                for connection in loop['connections']:
                                                    pair = connection['residues']
                                                    if len(pair) != 2:
                                                        closed = False
                                                    elif pair[1] != pair[0] + 1 or not first_edge <= pair[0] <= last_edge or pair[0] in edges:
                                                        closed = False
                                                    else:
                                                        edges = edges + [pair[0]]
                                                    distance = connection['distance_A']
                                                    if connection['missing_c'] or connection['missing_n'] or not connection['polymer_edge_present']:
                                                        closed = False
                                                    if not distance['available'] or distance['value'] is None:
                                                        closed = False
                                                    elif not 1.2 <= distance['value'] <= 1.5:
                                                        closed = False
                                                if len(edges) != max(0, last_edge - first_edge + 1):
                                                    closed = False
                                        if len(loop_ids) != len(intervals):
                                            closed = False
                                if closed:
                                    decision = {
                                        'mode': 'temperature',
                                        'probability': None,
                                        'temperature_multiplier': 0.75
                                    }

    elif event == 'retain':
        # No measured retention-gap evidence justifies replacing native low.
        decision = {'save_slot': None, 'state': 'current'}
    else:
        decision = {'state': 'native_low', 'slot': None}

    return {'decision': decision, 'memory': memory}
