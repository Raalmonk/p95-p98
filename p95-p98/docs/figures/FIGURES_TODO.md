# Figures to make

These are the figures the docs leave room for. Each one has a placeholder block in the docs, marked with `<!-- FIGURE PLACEHOLDER: <id> -->`. To add a figure:

1. Save the image at the path listed below.
2. In each doc listed under "Used in", replace the placeholder block (the HTML comment plus the quoted lines under it) with the `![...](...)` line it shows.
3. If the placeholder says a text diagram can be removed, delete that text diagram too.

Two existing figures, `Training_Workflow_NGK.svg` and `method_comparison.png`, are already embedded and need no work.

| Priority | Figure | Type | File | Used in |
|---|---|---|---|---|
| high | [How the programs were found, then deployed](#search-loop) | flowchart | `search_loop.svg` | `README.md`, `p95-p98/docs/closeout/DISCOVERY.md` |
| high | [What loop modeling and RMSD mean](#loop-and-rmsd) | illustration | `loop_and_rmsd.svg` | `README.md` |
| high | [New proteins: CPU vs accuracy, by starting model](#casp15-quality-cost) | chart | `casp15_quality_cost.svg` | `README.md`, `p95-p98/README.md`, `p95-p98/docs/closeout/casp15/INTERPRETATION.md` |
| high | [P98 stopped early on AlphaFold2 starts](#casp15-early-stopping) | chart | `casp15_early_stopping.svg` | `p95-p98/docs/closeout/casp15/INTERPRETATION.md`, `p95-p98/docs/RESEARCH_OVERVIEW.md` |
| medium | [BENCH48: better on W/S, worse on hard inputs](#bench48-subgroup-deltas) | chart | `bench48_subgroup_deltas.svg` | `p95-p98/docs/closeout/RESULTS.md` |
| medium | [What the frozen program sees and controls](#decide-interface) | diagram | `decide_interface.svg` | `p95-p98/docs/METHOD.md` |
| medium | [Install layout: two Python environments](#runtime-architecture) | diagram | `runtime_architecture.svg` | `p95-p98/README.md`, `p95-p98/docs/PROMOD3.md` |
| low | [What each cost number counts](#cost-boundaries) | diagram | `cost_boundaries.svg` | `p95-p98/docs/closeout/RESULTS.md` |

<a id="search-loop"></a>
## How the programs were found, then deployed

- **ID:** `search-loop`
- **Type:** flowchart, high priority
- **Save as:** `p95-p98/docs/figures/search_loop.svg`

**What it shows.** A simple loop flowchart labelled 'OpenEvolve search loop', with each box coloured by who does that step (people / LLM / host software). People define the one editable function decide(view), what it may observe, five scoring objectives and the budgets. The LLM proposes a code edit after seeing a parent program, a few peer programs and feedback scores. The host applies the patch, runs static and interface checks, runs native Rosetta NGK/ProMod3 on the 48 BENCH48 inputs, scores the results and updates the archive. An arrow back to the LLM closes the loop: about 100 proposals, at most two at a time, with a small tag '101 starts -> 100 returned -> 99 evaluated'. An exit arrow crosses a dashed 'discovery | deployment' line to four steps: pick P95 and P98, freeze them, test them on new proteins (CASP15), and run them as ordinary CPU code with no LLM calls. Keep it much simpler than Training_Workflow_NGK.svg and leave out the NGK inner loop.

**Where the content comes from.** README.md 'The idea' ASCII flowchart (the ```text block) and the OpenEvolve paragraph below it; DISCOVERY.md 'Who did what, and the rules of the search' (roles of people, LLM and host; what the LLM saw; five objectives; budgets; at most 100 proposals after P1, at most two at a time, wave by wave) and 'The counts' table (101 starts, 100 returned, 99 evaluated); RESEARCH_OVERVIEW.md 'The idea in one minute'.

**Used in:**

- `README.md`: Goes directly above the ASCII flowchart (the ```text block) and replaces it. Delete that block once the image exists. Path from the root: p95-p98/docs/figures/search_loop.svg
- `p95-p98/docs/closeout/DISCOVERY.md`: Adds to the three 'people / LLM / host' paragraphs by showing who does each step of the loop. Path: ../figures/search_loop.svg

<a id="loop-and-rmsd"></a>
## What loop modeling and RMSD mean

- **ID:** `loop-and-rmsd`
- **Type:** illustration, high priority
- **Save as:** `p95-p98/docs/figures/loop_and_rmsd.svg`

**What it shows.** A two-panel schematic, not real data. (A) A protein drawn as a grey fixed scaffold with one coloured loop whose two ends stay attached. Several faint alternative loop shapes show NGK trying candidates, with KIC closure keeping the ends connected, and each candidate carries an energy score. (B) A modelled loop laid over the experimental loop, with short lines joining matching atoms. RMSD is the root-mean-square of those distances in Å, and lower is better. Label 'local' (the loop region) and 'global' (the whole protein). Add a small note that the lowest-energy shape is not necessarily the one closest to the experimental structure.

**Where the content comes from.** README.md 'The idea' paragraphs and the RMSD definition at the start of 'What we found'; p95-p98/README.md 'Method' term list (NGK, KIC, Monte Carlo); casp15/INTERPRETATION.md 'Terms' and 'How we measured' (local backbone window vs global CA); RESULTS.md 'Metric definitions'; RESEARCH_OVERVIEW.md section 3 (more sampling may lower energy without getting closer to the experimental structure).

**Used in:**

- `README.md`: Illustrates the 'The idea' paragraph and the RMSD definition later in 'What we found', for readers new to protein modeling. Panel B's energy-vs-accuracy note sets up the next paragraph. Path from the root: p95-p98/docs/figures/loop_and_rmsd.svg

<a id="casp15-quality-cost"></a>
## New proteins: CPU vs accuracy, by starting model

- **ID:** `casp15-quality-cost`
- **Type:** chart, high priority
- **Save as:** `p95-p98/docs/figures/casp15_quality_cost.svg`

**What it shows.** Two side-by-side scatter panels: AlphaFold2 starts (n=6) and ESMFold starts (n=6). Both panels share one linear x-axis, mean method CPU per input from 0 to 260 s. The y-axis is mean local backbone RMSD in Å (lower is better). Each panel spans the same 0.4 Å (e.g. 1.55-1.95 and 5.40-5.80), so small gaps are not exaggerated. Plot one labelled point per method: P95 and P98 in blue, native and short warm-start NGK in grey. Each label gives the exact CPU in seconds, the RMSD and the CPU as a % of native NGK. A dashed horizontal line marks the untouched starting models; every method ends above that line in both panels. The message: on AlphaFold2 starts, P98 sits far left with slightly better accuracy than native NGK (6.66% of its CPU). On ESMFold starts, P98 moves to the far right (151.50%).

**Where the content comes from.** casp15/INTERPRETATION.md 'Results on new proteins' table. AlphaFold2: source 1.5963 Å; P95 98.587 s / 1.7548 Å (45.44%); P98 14.448 s / 1.6016 Å (6.66%); native NGK 216.944 s / 1.6297 Å (100%); short NGK 48.436 s / 1.8174 Å (22.33%). ESMFold: source 5.4328 Å; P95 191.199 s / 5.7553 Å (117.11%); P98 247.341 s / 5.7425 Å (151.50%); native NGK 163.264 s / 5.7804 Å (100%); short NGK 34.712 s / 5.6971 Å (21.26%). Ratios re-checked from the means. Recompute with docs/closeout/casp15/summarize.py.

**Used in:**

- `README.md`: Charts the table above with P95 and the short baseline added, and makes the ESMFold limit visible. Leave a blank line before the image so it isn't absorbed into the table. Path from the root: p95-p98/docs/figures/casp15_quality_cost.svg
- `p95-p98/README.md`: Charts the CASP15 table above, matching how the BENCH48 section has method_comparison.png. Leave a blank line before the image so it isn't absorbed into the table. Path: docs/figures/casp15_quality_cost.svg
- `p95-p98/docs/closeout/casp15/INTERPRETATION.md`: Charts the 15-row table above, split by starting model. Leave a blank line before the image so it isn't absorbed into the table. Path: ../../figures/casp15_quality_cost.svg

<a id="casp15-early-stopping"></a>
## P98 stopped early on AlphaFold2 starts

- **ID:** `casp15-early-stopping`
- **Type:** chart, high priority
- **Save as:** `p95-p98/docs/figures/casp15_early_stopping.svg`

**What it shows.** Panel A (AlphaFold2 starts): for each of the six targets, two horizontal bars in seconds, P98 CPU (blue) and native warm-start NGK CPU (grey). Write P98's KIC-attempt count and 'stopped early' next to its bar. Panel B (ESMFold starts, T1123 and T1139 only): the same pair of bars, labelled '800 KIC attempts, no stop'. Here P98's bar is longer than NGK's. Both panels share one x-axis (0-500 s) so the bars can be compared directly. The caption should say that zero KIC attempts does not mean zero work (setup, sidechain steps and minimization still run), and that panel B shows only the two ESMFold runs the docs discuss. Don't add KIC counts for native NGK: the docs don't report them.

**Where the content comes from.** casp15/INTERPRETATION.md 'The program really did stop sampling' table: T1104 0 KIC, 8.723 vs 91.857 s; T1109 0, 12.798 vs 251.427 s; T1123 13, 25.173 vs 334.972 s; T1139 2, 10.989 vs 237.498 s; T1187 0, 11.464 vs 242.887 s; T1194 27, 17.540 vs 143.024 s (means 14.448 vs 216.944 s = 6.66%). The ESMFold paragraph after it: T1123 310.126 vs 75.744 s; T1139 487.209 vs 204.293 s; 800 KIC attempts and no voluntary stop for each (consistent with the per-protein means in casp15/REPORT.md). Raw counters: casp15/mc_control_counts.csv.

**Used in:**

- `p95-p98/docs/closeout/casp15/INTERPRETATION.md`: Charts both the per-target stop table and this ESMFold paragraph. Path: ../../figures/casp15_early_stopping.svg
- `p95-p98/docs/RESEARCH_OVERVIEW.md`: Shows the stopping behaviour behind the 6.66% claim, plus panel B's ESMFold contrast for the 'Two limits' list just below. Path: figures/casp15_early_stopping.svg

<a id="bench48-subgroup-deltas"></a>
## BENCH48: better on W/S, worse on hard inputs

- **ID:** `bench48-subgroup-deltas`
- **Type:** chart, medium priority
- **Save as:** `p95-p98/docs/figures/bench48_subgroup_deltas.svg`

**What it shows.** Diverging horizontal bars of the mean paired change versus NGK, in Å (method minus NGK; left of zero means closer to the experimental structure than NGK). Draw two small panels, local RMSD and global RMSD, each with four bars: P95 W/S (n=32), P98 W/S (n=32), P95 hard (n=15) and P98 hard (n=15). Local values: -0.177, -0.035, +0.874, +0.353. Global values: -0.069, -0.014, +0.216, +0.107. The message: small gains on W/S inputs, bigger losses on hard inputs. The caption should say that these use the frozen raw RMSD, which is defined differently for W/S (backbone atoms, expanded region) and hard (CA atoms, loop union), so compare within a group, not across groups. It should also say that NGK's one invalid hard result is excluded, and that these are not the display CA medians in the README table, where both programs look better than NGK.

**Where the content comes from.** results/TABLES.md paired-change table: P95 WS local -0.177382 / global -0.069089 (32/32); P95 hard +0.873826 / +0.216342 (15/16); P98 WS -0.035327 / -0.014386 (32/32); P98 hard +0.352907 / +0.107234 (15/16). Definitions: RESULTS.md 'Metric definitions'. Recompute with docs/closeout/results/summarize.py.

**Used in:**

- `p95-p98/docs/closeout/RESULTS.md`: Charts the hard-group caveat from the 'What to notice' list. The numbers are otherwise only in results/TABLES.md. Anchored on the list's last bullet so the list isn't split; leave a blank line before the image. Path: ../figures/bench48_subgroup_deltas.svg

<a id="decide-interface"></a>
## What the frozen program sees and controls

- **ID:** `decide-interface`
- **Type:** diagram, medium priority
- **Save as:** `p95-p98/docs/figures/decide_interface.svg`

**What it shows.** On the left, the host packs a 'view' into decide(view). The view holds the event; an observation (starting and current geometry, fixed energies, per-loop and per-residue data, remaining budget, available actions, limited history), computed only from the input structure and current candidates; and memory. In the centre, frozen P95/P98 return a decision plus updated memory. On the right, the decision fans out to two levels. Outer routing: choose an action (ProMod3 database lookup, NGK refine, NGK rebuild, minimize, deliver), choose the parent structure, keep candidates. Inner NGK callbacks: stop early, and use native acceptance or temperature x 0.75. Behind a wall outside the flow, a box labelled 'never enters a running program' lists reference coordinates, reference RMSD, benchmark labels, PDB/file IDs, offline evaluation results and AlphaFold confidence scores. Optionally, show in grey the options the interface allowed but P95/P98 don't use: direct acceptance probability, custom inner save/restore and non-native KIC moves. Focus on the information boundary, and don't redraw the NGK loop from Training_Workflow_NGK.svg.

**Where the content comes from.** METHOD.md intro (event / observation / memory; outer routing; inner callbacks; unused options) and 'What the program can see'; DISCOVERY.md 'What the program could and couldn't touch' paragraph and its allowed-vs-used table; casp15/INTERPRETATION.md notes under the stop table (stopping rules never saw reference RMSD or AlphaFold confidence scores).

**Used in:**

- `p95-p98/docs/METHOD.md`: Pictures the event/observation/memory list and the two-level bullets above, and previews 'What the program can see'. Path: figures/decide_interface.svg

<a id="runtime-architecture"></a>
## Install layout: two Python environments

- **ID:** `runtime-architecture`
- **Type:** diagram, medium priority
- **Save as:** `p95-p98/docs/figures/runtime_architecture.svg`

**What it shows.** Data flow of one P95/P98 run. Left: the host process (Linux x86-64, Python 3.12), holding the p95p98 CLI, the frozen policy, the legacy NGK scheduler and the licensed PyRosetta 2026.03 wheel. Right: the ProMod3 worker (Python 3.14, ProMod3 3.7.0 + OpenStructure 2.12.0), started through the --promod-python wrapper with p95-p98/src on PYTHONPATH. The two processes exchange only PDB and JSON files. Inputs arrive from the top: the input JSON with a complete PDB and target sequence, plus the work profile (reference tariff) and the CPU/wall budget. A resources/ folder (manifest, filter ledger, StructureDB, FragDB) is built once beforehand by build_resources from protected.json, excluding the input. Outputs leave at the bottom: final.pdb, result.json, endpoint.json.gz, route_steps/ and actions/. Mark the version and hash checks each side runs before modeling.

**Where the content comes from.** p95-p98/README.md 'Installation', 'Run a public example', 'Outputs'; PROMOD3.md 'Versions', 'Install ProMod3' steps 3-5, 'Build a library that excludes your input' (steps 1-3 and the pre-modeling SHA256/ledger check); NATIVE_RUNTIME.md 'Set up the runtime' (host checks the runtime version).

**Used in:**

- `p95-p98/README.md`: Pictures install step 3 (the separate ProMod3 worker environment) and previews the Run and Outputs sections. Path: docs/figures/runtime_architecture.svg
- `p95-p98/docs/PROMOD3.md`: Pictures the separate-environments explanation, the PYTHONPATH wrapper (install steps 3-5) and the one-time resource build. Path: figures/runtime_architecture.svg

<a id="cost-boundaries"></a>
## What each cost number counts

- **ID:** `cost-boundaries`
- **Type:** diagram, low priority
- **Save as:** `p95-p98/docs/figures/cost_boundaries.svg`

**What it shows.** A left-to-right strip of four stages. Each stage is a box listing the cost numbers the docs report for it, with their units. (1) Discovering the programs, once: 380.437 route-CPU hours for scoring proposals; 21,531,286 LLM tokens (P96 missing); zero paid API calls; LLM wait time and money not reconciled. (2) Building the ProMod3 library, once per input set: 148.44 CPU s for CASP15 and 29.36 CPU s for the 1L2Y example; the BENCH48 build is not reconciled. (3) Running a program on an input, three measures: BENCH48 logical work, in tariff units not seconds (P95 16.11%, P98 25.13% of NGK); BENCH48 accounted route CPU, in seconds, including failed attempts and reused preparation (17.84% and 26.66% of NGK); and CASP15 method CPU, covering the policy and its observations (P98 6.66% of native NGK on AlphaFold2 starts, with 156.18 s of earlier repair attempts kept separately). (4) Evaluating results: final quality scoring, MolProbity, preflight and scoring of starting models. A bracket over box 3 only reads 'used in program-vs-NGK comparisons'. A banner says to compare numbers only within one box and one unit.

**Where the content comes from.** RESULTS.md 'Cost boundaries' (bullets and the 'Discovery costs are separate' paragraph); results/TABLES.md cost-ratio table (sum ratios 16.113416% / 17.842394% for P95, 25.130934% / 26.658927% for P98); casp15/INTERPRETATION.md 'What counts as cost, and other caveats'; casp15/REPORT.md 'Other CPU costs' (resource build 148.439991 s, preflight, evaluations); VALIDATION.md 'ProMod library for the example' (29.36 CPU s); README.md CPU-time paragraph under 'On new proteins'.

**Used in:**

- `p95-p98/docs/closeout/RESULTS.md`: An overview placed before the 7-column cost table and the discovery-costs paragraph, so readers don't directly compare logical work, route CPU, CASP15 method CPU and discovery cost. RESEARCH_OVERVIEW.md section 6 already links here as 'Cost definitions'. Path: ../figures/cost_boundaries.svg
