def decide(view):
    # One unevaluated recombination: broad bounded startup and measured
    # startup reassessment, preserving paired patience and one descent only.
    # Same-binding peer 321cc837 improves four component-balanced quality
    # objectives over current but loses efficiency; its mechanisms are not
    # separately identified. Do not transfer its additional descent.
    # Paired WS effects versus matched NGK favor RMSD, not energies;
    # hard both-valid RMSD regresses. Preserve the existing repair route.
    # Supplied endpoints are 48/48 VALID with complete MP and no timeouts.
    # Full paired row/component tables and retention-quality scores are absent.
    # Minimize has a scored example; startup and database intermediates do not.
    # Direct-parent availability conflicts between the current card and log.
    # TRAIN48 covers 32 components with uneven, incomplete routing coverage.
    # No evaluator is exposed here; this proposal has no measured gains.
    # CPU, logical work, waiting and offline scoring remain separate.
    # Neither source proximity nor hardware speed establishes quality gains.
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
                if source['fixed_local_energy'] is None or source['fixed_global_energy'] is None:
                    gentle = False

                # Flank energy alone need not justify backbone sampling.
                # Require complete movable-residue coverage before using
                # this broader descent-first gate; unknown is not favorable.
                intervals = []
                if 'loop_intervals' in source and source['loop_intervals'] is not None:
                    intervals = source['loop_intervals']
                movable = {}
                if len(intervals) == 0:
                    gentle = False
                for interval in intervals:
                    if interval[1] < interval[0]:
                        gentle = False
                    else:
                        for index in range(interval[0], interval[1] + 1):
                            movable[str(index)] = False

                # Every loop must independently have nonpositive energy.
                # Neither cancellation between loops nor favorable flanks
                # may conceal a strained movable region.
                if 'per_loop' not in source or source['per_loop'] is None:
                    gentle = False
                else:
                    if len(source['per_loop']) == 0 or len(source['per_loop']) != len(intervals):
                        gentle = False
                    loop_ids = []
                    for loop in source['per_loop']:
                        if 'loop_index' not in loop or loop['loop_index'] is None:
                            gentle = False
                        else:
                            index = loop['loop_index']
                            if not 0 <= index < len(intervals) or index in loop_ids:
                                gentle = False
                            else:
                                loop_ids = loop_ids + [index]
                        if 'fixed_energy' not in loop or loop['fixed_energy'] is None:
                            gentle = False
                        elif loop['fixed_energy'] > 0.0:
                            gentle = False
                    if len(loop_ids) != len(intervals):
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
                        if 'index' not in residue or residue['index'] is None:
                            gentle = False
                        else:
                            key = str(residue['index'])
                            if key in movable:
                                if movable[key]:
                                    gentle = False
                                movable[key] = True
                                if 'fixed_energy' in residue and residue['fixed_energy'] is not None:
                                    if residue['fixed_energy'] > 5.0:
                                        gentle = False
                for key in movable:
                    if not movable[key]:
                        gentle = False

                # Transfer bounded native startup to fully gentle neighborhoods.
                # Complete low-strain loops permit startup, not backbone search.
                # Missing evidence leaves ordinary bounded refinement available.
                routing['startup_only'] = gentle

                # Only live parent-specific capabilities may execute.
                # Descent remains the fallback when refinement is unavailable.
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
            # One qualified descent also follows dynamically resolved startup.
            # Select from actual outer endpoint diagnostics, not inner minima.
            # Keep RAW and the incumbent; do not repeat descent.
            if best['source']['geometry_valid'] is True and observation['remaining_work'] > 24.0:
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
            if strained and observation['remaining_work'] > 24.0:
                names = ['minimize']

        left = observation['remaining_work']
        origin = routing['initial_remaining']
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
            eligible = name not in attempts
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
                                        raw_valid
                                        and 'startup_only' in routing
                                        and routing['startup_only']
                                        and name == 'ngk_refine'
                                    ),
                                    'startup_done': False,
                                    'startup_before': None,
                                    'startup_checked': False,
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
            # Stop alone after the startup acceptance callback, regardless
            # of its native outcome, or before the first loop choice.
            # No extra operation is required to complete startup. The outer
            # allowance, preparation charges and delivery reserve persist.
            if 'startup_only' in control and control['startup_only'] and (
                control['startup_done'] or observation['site'] == 'choose_loop'
            ):
                decision['stop'] = True
            elif left is not None:
                if left <= control['cutoff']:
                    decision['stop'] = True
                elif observation['site'] == 'choose_loop' and not control['repair']:
                    state = observation['accepted_current']
                    if state is None:
                        state = observation['working_state']
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
                            control['progress_local'] = local_energy
                            control['progress_left'] = left
                        else:
                            # Keep independent diagnostic minima, but renew
                            # patience only from one actually observed state.
                            # Alternating incompatible energy improvements
                            # must not jointly manufacture continuing progress.
                            # Fixed weights remain comparable across epochs.
                            control['low_global'] = min(control['low_global'], global_energy)
                            control['low_local'] = min(control['low_local'], local_energy)
                            progress = False
                            if global_energy <= control['progress_global'] and local_energy <= control['progress_local']:
                                if global_energy < control['progress_global'] - 0.5 or local_energy < control['progress_local'] - 0.25:
                                    progress = True
                            if progress:
                                control['progress_global'] = global_energy
                                control['progress_local'] = local_energy
                                control['progress_left'] = left

                            history = observation['history']
                            spent = control['origin'] - left
                            stalled = control['progress_left'] - left
                            # Separate progress traces, not a synthetic state
                            # combining minima from different visits.
                            if history is not None and len(history) >= 16:
                                if spent >= 0.10 * control['origin'] and stalled >= max(48.0, 0.06 * control['origin']):
                                    decision['stop'] = True

            # Reassess once before backbone sampling. Stop protections above
            # take priority. Unknown or incomplete evidence leaves MC unchanged.
            if not decision['stop'] and not control['repair'] and not control['startup_only']:
                if observation['site'] == 'choose_loop' and not control['startup_checked']:
                    control['startup_checked'] = True
                    state = observation['accepted_current']
                    before = control['startup_before']
                    intervals = observation['loop_intervals_zero_based']
                    # Require an explicitly observed accepted state: do not
                    # substitute a possibly rejected working candidate.
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

                    # Compare two actual states under fixed evaluation weights.
                    # Require both aggregate improvements and no loop regression.
                    if ready:
                        global_energy = state['fixed']['total']
                        if global_energy is None:
                            ready = False
                        else:
                            ready = (
                                global_energy < before['global'] - 0.5
                                and sum([after[key] for key in after])
                                < sum([before['loops'][key] for key in before['loops']]) - 0.25
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

                                # Absolute source displacement bounds intervention;
                                # it is not target RMSD or a pairwise displacement.
                                displacement = loop['ca_displacement_max_A']
                                if not displacement['available'] or displacement['value'] is None:
                                    ready = False
                                elif not 0 <= displacement['value'] <= 0.5:
                                    ready = False
                                if loop['ca_displacement_missing_count'] != 0 or loop['ca_displacement_observed_count'] != expected:
                                    ready = False

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
                        # Stop alone; preserve native-low delivery and outer
                        # endpoint qualification. No restore or budget renewal.
                        control['startup_resolved'] = True
                        decision['stop'] = True

    elif event == 'accept':
        decision = {'mode': 'native', 'probability': None, 'temperature_multiplier': None}
        startup_only = False
        if 'ngk_control' in memory:
            control = memory['ngk_control']
            startup_only = 'startup_only' in control and control['startup_only']
            if observation['site'] == 'initial_repack':
                # This callback precedes acceptance. Capture the previous
                # accepted state, never label the candidate as accepted.
                control['startup_done'] = True
                if not control['repair'] and not startup_only:
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
                            # Bounded diagnostic memory, not an archive slot.
                            control['startup_before'] = {
                                'observed_step': observation['step'],
                                'global': current['fixed']['total'],
                                'loops': values
                            }
        if 'ngk_control' in memory and not memory['ngk_control']['repair'] and not startup_only:
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
                            before = sum([
                                loop['fixed_energy'] for loop in current['loop_energies']
                            ])
                            after = sum([
                                loop['fixed_energy'] for loop in candidate['loop_energies']
                            ])
                            if after > before:
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
