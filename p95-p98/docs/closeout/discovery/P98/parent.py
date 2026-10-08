def decide(view):
    # One unevaluated crossover; no evaluator is exposed here.
    # Same-binding peers show separate quality/work tradeoffs and 48/48
    # valid endpoints versus the current 46/48, not universal dominance.
    # Combine one qualified endpoint polish with cross-epoch fixed-score
    # stopping. This combination's five-axis effects remain unmeasured.
    # Full rowwise/component-paired effects and scored retention gaps are
    # unavailable. TRAIN48 covers 32 components with uneven state coverage.
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
                'attempts': []
            }
        routing = memory['routing']
        attempts = routing['attempts']
        raw_valid = raw['source']['geometry_valid'] is True

        # Preserve RAW and compare each retained state's own measurements.
        # Neither validity nor energy dominance establishes target accuracy.
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
        cleanup_only = False
        polish = False

        if len(attempts) == 0:
            if raw_valid:
                names = ['ngk_refine', 'minimize']
                source = raw['source']
                loops = source['per_loop'] if 'per_loop' in source and source['per_loop'] is not None else []
                intervals = source['loop_intervals'] if 'loop_intervals' in source and source['loop_intervals'] is not None else []
                residues = source['per_residue'] if 'per_residue' in source and source['per_residue'] is not None else []
                sequence = source['sequence'] if 'sequence' in source and source['sequence'] is not None else ''
                cleanup_only = len(intervals) > 0 and len(loops) == len(intervals)
                expected = sum([interval[1] - interval[0] + 1 for interval in intervals])
                observed = []

                # Initialization-only cleanup requires complete, low-strain,
                # source-conservative evidence. Missing displacement is unknown.
                for loop in loops:
                    if 'fixed_energy' not in loop or loop['fixed_energy'] is None:
                        cleanup_only = False
                    elif loop['fixed_energy'] > 0.0:
                        cleanup_only = False
                    if 'source_displacement_A' not in loop or loop['source_displacement_A'] is None:
                        cleanup_only = False
                    elif not 0.0 <= loop['source_displacement_A'] <= 0.5:
                        cleanup_only = False

                for residue in residues:
                    in_loop = False
                    if 'index' in residue and residue['index'] is not None:
                        index = residue['index']
                        for interval in intervals:
                            if interval[0] <= index <= interval[1]:
                                in_loop = True
                    if in_loop:
                        if index not in observed:
                            observed = observed + [index]
                        if 'missing' not in residue or residue['missing'] is not False:
                            cleanup_only = False
                        if 'fixed_energy' not in residue or residue['fixed_energy'] is None:
                            cleanup_only = False
                        elif residue['fixed_energy'] > 5.0:
                            cleanup_only = False
                        if 'source_displacement_A' not in residue or residue['source_displacement_A'] is None:
                            cleanup_only = False
                        elif not 0.0 <= residue['source_displacement_A'] <= 1.0:
                            cleanup_only = False
                        if 'omega' not in residue or residue['omega'] is None:
                            cleanup_only = False
                        else:
                            omega = abs(residue['omega'])
                            trans = abs(180.0 - omega) <= 30.0
                            cis_proline = False
                            if 0 <= index + 1 < len(sequence):
                                cis_proline = omega <= 30.0 and sequence[index + 1] == 'P'
                            if not trans and not cis_proline:
                                cleanup_only = False
                if expected <= 0 or len(observed) != expected:
                    cleanup_only = False
            else:
                names = ['promod3_database', 'ngk_rebuild',
                         'ngk_refine', 'minimize']
        elif best['source']['geometry_valid'] is not True and len(attempts) < 3:
            names = ['promod3_database', 'ngk_rebuild',
                     'ngk_refine', 'minimize']
        elif best['source']['geometry_valid'] is True and len(attempts) < 3:
            if 'minimize' not in attempts:
                if best['source']['fixed_global_energy'] is not None:
                    if best['source']['fixed_local_energy'] is not None:
                        # One polish after either refinement or repair.
                        # Keep its actual parent as a delivery alternative.
                        # Negative energy alone does not prohibit descent.
                        polish = True
                        names = ['minimize']

        left = observation['remaining_work']
        origin = routing['initial_remaining']
        cutoff = max(24.0, origin * (0.60 if raw_valid else 0.15))
        ngk_used = 'ngk_refine' in attempts or 'ngk_rebuild' in attempts

        for name in names:
            is_ngk = name in ['ngk_refine', 'ngk_rebuild']
            eligible = name not in attempts
            if is_ngk and (ngk_used or left <= cutoff):
                eligible = False
            if polish and left <= max(24.0, 0.03 * origin):
                eligible = False
            if eligible:
                selected_parent = best['slot'] if polish else 0
                for cap in observation['available_actions']:
                    if cap['name'] == name and selected_parent in cap['parent_slots']:
                        required = [0]
                        if best['slot'] != 0:
                            required = required + [best['slot']]
                        if selected_parent not in required:
                            required = required + [selected_parent]
                        capacity = 9 - cap['max_outputs']
                        price = cap['maximum_work']
                        # Availability qualifies this exact parent and profile.
                        # Only qualified minimization uses a child; database/MC
                        # retain frozen RAW-derived inputs and host-owned
                        # preparation, specialist and reuse charges.
                        # CPU/wall protection and delivery reserves are separate
                        # host constraints, not renewed logical allowances.
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
                                    'cleanup_only': cleanup_only,
                                    'cleanup_ready': False,
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
            if left is not None:
                if left <= control['cutoff']:
                    decision['stop'] = True
                elif control['cleanup_only'] and control['cleanup_ready']:
                    # Initialization acceptance has resolved. Stop alone.
                    decision['stop'] = True
                elif observation['site'] == 'choose_loop':
                    state = observation['accepted_current']
                    if state is None:
                        state = observation['working_state']
                    if state is not None and len(state['loop_energies']) > 0:
                        global_energy = state['fixed']['total']
                        local_energy = sum([loop['fixed_energy'] for loop in state['loop_energies']])
                        movable_count = sum([
                            interval[1] - interval[0] + 1
                            for interval in observation['loop_intervals_zero_based']
                        ])
                        global_step = max(0.5, 0.05 * movable_count)
                        local_step = max(0.25, 0.025 * movable_count)

                        # Fixed-weight milestones remain comparable across
                        # score epochs. Schedule changes do not renew patience.
                        # Independent minima are progress traces, not a
                        # synthetic archived structure or reference estimate.
                        if control['low_global'] is None:
                            control['low_global'] = global_energy
                            control['low_local'] = local_energy
                            control['progress_left'] = left
                        else:
                            progress = False
                            if global_energy < control['low_global'] - global_step:
                                control['low_global'] = global_energy
                                progress = True
                            if local_energy < control['low_local'] - local_step:
                                control['low_local'] = local_energy
                                progress = True
                            if progress:
                                control['progress_left'] = left
                            history = observation['history']
                            spent = control['origin'] - left
                            stalled = control['progress_left'] - left
                            if not control['repair'] and history is not None and len(history) >= 16:
                                if spent >= 0.15 * control['origin'] and stalled >= max(48.0, 0.08 * control['origin']):
                                    decision['stop'] = True

    elif event == 'accept':
        decision = {'mode': 'native', 'probability': None, 'temperature_multiplier': None}
        if 'ngk_control' in memory:
            control = memory['ngk_control']
            if control['cleanup_only'] and observation['site'] == 'initial_repack':
                control['cleanup_ready'] = True
            if not control['repair'] and not control['cleanup_only']:
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
                                before = sum([loop['fixed_energy'] for loop in current['loop_energies']])
                                after = sum([loop['fixed_energy'] for loop in candidate['loop_energies']])
                                if after > before:
                                    decision = {'mode': 'temperature', 'probability': None,
                                                'temperature_multiplier': 0.75}

    elif event == 'retain':
        # No scored retention-gap evidence: retain native behavior.
        decision = {'save_slot': None, 'state': 'current'}
    else:
        decision = {'state': 'native_low', 'slot': None}

    return {'decision': decision, 'memory': memory}
