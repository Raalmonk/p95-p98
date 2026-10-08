# P95 / P98: control programs found by LLM-guided program search

P95 and P98 are the programs produced by NGNGK, a study of program search guided by a large language model (LLM) for protein-loop modeling. The search used OpenEvolve to propose and score rules for a modeling workflow: which operation to try, which candidate to keep and when to stop computing. The programs we picked run without any LLM.

The names come from proposals 95 and 98 in one bounded run of about 100 candidates. The run recorded 101 model starts, 100 returned programs and 99 legal programs that we evaluated. P95 and P98 are Python control programs, and you can read their source. The search kept the language model's weights fixed. It didn't show that the search converged, and it didn't try every possible program.

A Python host runs the frozen programs, giving them observations of the starting structure, the search history and a limited budget. Native Rosetta/NGK and ProMod3 do the actual science. You don't need an LLM account or OpenEvolve to run P95/P98.

[Research idea and why it matters](docs/RESEARCH_OVERVIEW.md) · [How the programs were found](docs/closeout/DISCOVERY.md) · [Installation](#installation) · [Input format](#inputs)

## Method

![Program discovery, routing and the controlled NGK refinement loop](docs/figures/Training_Workflow_NGK.svg)

The figure shows program discovery and deployment as separate stages.

Some terms used below:

- NGK (next-generation kinematic closure) is a Rosetta method for remodeling a protein loop.
- KIC (kinematic closure) is the step inside NGK that reshapes a loop while keeping its ends attached.
- Monte Carlo sampling makes random moves and sometimes accepts a worse one, so the search doesn't get stuck. A "temperature" setting controls how often that happens.

The searched rules control three things: which outer action to take, which candidate to keep, and when to stop based on history. Inside NGK, P95/P98 either use Rosetta's own acceptance rule or, under some conditions, multiply the temperature by 0.75. The underlying tools provide KIC closure, structural moves, sidechain operations and NGK's usual return of its lowest-energy structure.

## External Monte Carlo control

On six external CASP15 targets starting from AlphaFold2 models, P98 used 6.66% of the measured CPU time (computer processing time) of native warm-start NGK, with slightly lower mean local backbone RMSD (1.602 vs. 1.630 Å), and never called the database.

CASP15 is a structure-prediction benchmark; these six targets are outside the development set used in the search. "Local backbone RMSD" (root-mean-square deviation) measures how far the modeled loop's backbone atoms are from the experimental structure, in ångströms. Lower is better.

P98 stopped all six runs early during NGK refinement, after 0, 0, 13, 2, 0 and 27 KIC attempts. So the programs can cut the cost of native sampling, mainly by stopping early, without using the database.

| Starting models | P98 mean CPU | Native NGK mean CPU | P98 / NGK CPU | Source local RMSD | P98 local RMSD | NGK local RMSD |
|---|---:|---:|---:|---:|---:|---:|
| AlphaFold2, six targets | 14.45 s | 216.94 s | 6.66% | 1.596 Å | 1.602 Å | 1.630 Å |
| ESMFold, same six targets | 247.34 s | 163.26 s | 151.50% | 5.433 Å | 5.743 Å | 5.780 Å |
| All 12 inputs | 130.89 s | 190.10 s | 68.85% | 3.515 Å | 3.672 Å | 3.705 Å |

![New proteins: CPU vs accuracy, by starting model](docs/figures/casp15_quality_cost.svg)

How the test was set up:

- We fixed both starting-model groups (AlphaFold2 and ESMFold) and chose P98 as the main candidate before seeing results.
- The 48 runs come from four frozen methods, six targets, two starting-model groups and one random seed (4 x 6 x 2 x 1 = 48).
- No shared NGK rebuild ran before the programs made their decisions, and neither P95 nor P98 chose a database action in any run.
- On AlphaFold2 starts, P98 also used 29.83% of the CPU of a short NGK run, with mean local RMSD 1.602 vs. 1.817 Å.

What this doesn't show:

- It doesn't show an improvement over AlphaFold2 itself. The CPU comparison is against extra NGK refinement. P98's mean local RMSD was 0.0053 Å worse than the untouched AlphaFold2 models.
- It doesn't always save compute. On ESMFold starts, P98 cost more than native NGK (151.50%).
- Refinement didn't beat the starting models: on the pooled inputs, every method's mean local RMSD was worse than the untreated starting model.
- The savings depend on the starting models. We don't claim refinement always helps, that the methods are statistically equivalent, or that the 0.75 temperature multiplier helps on its own.
- CPU seconds here and BENCH48 "logical work" (below) are different units.

[Interpretation and all comparisons](docs/closeout/casp15/INTERPRETATION.md) · [48-row results](docs/closeout/casp15/results_per_input.csv) · [Native MC counters](docs/closeout/casp15/mc_control_counts.csv) · [Recompute](docs/closeout/casp15/summarize.py)

## Development-set comparison

[![BENCH48 structural validity, recorded CPU and structural-quality distributions](docs/figures/method_comparison.png)](docs/figures/method_comparison.pdf)

The figure ([vector PDF](docs/figures/method_comparison.pdf)) shows results on BENCH48, our development set. Agent-Luna and Agent-Astra each have three inputs. Recorded CPU is the cost of running the programs, not the cost of the search that found them. Measurement definitions and sample counts are in the [figure caption](docs/figures/CAPTION.md).

### Recomputable development results

On BENCH48, P95 did 16% and P98 did 25% of NGK's work, and both returned 48 valid structures to NGK's 47. These are development results, not an independent test: we used the same 48 inputs (from 32 groups of related proteins) to search for and select the programs.

"Logical work" is the study's budget unit (operations priced by a tariff), not seconds. RMSD medians use the common scaffold-fit CA (alpha-carbon) definition for display. They are not the unitless objectives the search optimized.

| Method | Valid / planned | Total logical work | Work / NGK | Accounted route CPU (s) | Median local CA RMSD (Å) | Median global CA RMSD (Å) |
|---|---:|---:|---:|---:|---:|---:|
| P95 | 48 / 48 | 8,518.318 | 16.11% | 9,974.949 | 0.820 | 0.226 |
| P98 | 48 / 48 | 13,285.407 | 25.13% | 14,903.911 | 0.780 | 0.225 |
| Native NGK | 47 / 48 | 52,864.757 | 100% | 55,905.890 | 0.878 | 0.267 |

Across BENCH48, each program made 11 database calls, 37 NGK-refinement calls and 2 NGK-rebuild calls. One input can use more than one action. The [action-coverage records](docs/closeout/results/action_coverage.json) show that the programs used both database retrieval and NGK control. We did not measure how much of the savings came from retrieval specifically.

Notes on the numbers:

- All methods returned 48 endpoints. NGK's one invalid endpoint and the cost of every attempt are included.
- Accounted CPU keeps measured-cost reuse. It leaves out final scoring, MolProbity (a structure-quality checker), resource construction and time spent waiting on the LLM.
- An earlier figure of 8% is not supported for P95/P98 by the audited cost summaries.
- On the hard subgroup, raw RMSD is worse for both programs. Subgroup effects and all four raw quality metrics are in [the results report](docs/closeout/RESULTS.md).

[Research evidence index](docs/closeout/EVIDENCE_INDEX.md) ·
[Discovery evidence](docs/closeout/DISCOVERY.md) ·
[144-row data and summary command](docs/closeout/results/TABLES.md) ·
[Earlier General pilot and its limits](docs/closeout/GENERAL_PILOT.md) ·
[CASP15 supplement results](docs/closeout/casp15/REPORT.md) ·
[External MC-control interpretation](docs/closeout/casp15/INTERPRETATION.md)

The CASP15 test is separate from BENCH48 and from the older General pilot. Its 48 outputs passed our geometry checks, but we skipped MolProbity. [The complete report](docs/closeout/casp15/REPORT.md) covers both frozen programs, both native baselines, energies, global RMSDs and earlier repair costs we kept in the totals.

## Installation

Version 0.1.0 targets Linux x86-64 with Python 3.12.

1. Install the licensed PyRosetta `2026.03+releasequarterly.5e498f1409` wheel in your Python 3.12 environment.
2. Check out and install the package:

   ```sh
   git clone --filter=blob:none --sparse --branch codex/p95-p98 https://github.com/Raalmonk/p95-p98.git p95p98-rosetta
   cd p95p98-rosetta
   git sparse-checkout set p95-p98
   cd p95-p98
   python -m pip install .
   p95p98 verify
   ```

   This repo is a full fork of `RosettaCommons/rosetta`. The commands above check out only the `p95-p98/` package directory. If you have a full checkout, go into `p95-p98/` from the repo root before installing.
3. Set up the separate database/sampling worker. It uses ProMod3 3.7.0 and OpenStructure 2.12.0, and its Python environment can differ from PyRosetta's. Follow [native runtime installation](docs/NATIVE_RUNTIME.md) and [ProMod3 installation and resource construction](docs/PROMOD3.md) to get compatible dependencies and build a fragment library that excludes the source structures.

All branches need these dependencies; the host never quietly swaps in another method. No Rosetta C++ or native-binding patch is needed.

![Install layout: two Python environments](docs/figures/runtime_architecture.svg)

## Inputs

Give the program a complete, canonical protein PDB file and its target sequence. This release controls local search on prepared structures. It does not add residues to an incomplete PDB, so turn any insertion/deletion candidates into a complete structure with the target sequence first.

```json
{
  "structure": "1l2y_model1_A.pdb",
  "sequence": "NLYIQWLKDGGPSSGRPPPS",
  "loops": [{"start": 10, "stop": 15, "cut": 12, "extended": false}],
  "local_energy_residues": [10, 11, 12, 13, 14, 15],
  "seed": 20260922,
  "input_kind": "W"
}
```

Rules for this file:

- PDB paths are relative to the JSON file.
- Residue indices are one-based pose indices, not PDB residue numbers.
- Loops must not overlap, must be internal (not at a chain end) and must be at least three residues long.
- List the local energy region explicitly, and include every loop residue in it.
- `input_kind` records where the input came from (`W`, `S`, or `hard`). It is not a requested output quality. See [execution semantics](docs/METHOD.md).
- The prepared-input converter doesn't handle noncanonical residues, alternate conformers, insertion codes, disulfide-tagged inputs or terminal loops.

## Run a public example

1. Download the pinned public structure:

   ```sh
   python examples/fetch_1l2y.py --output examples/1l2y_model1_A.pdb
   ```

2. Build the resource library using `examples/protected.json`, as described in [the ProMod3 guide](docs/PROMOD3.md).
3. Run P95:

   ```sh
   p95p98 run \
     --input examples/1l2y.json \
     --policy P95 \
     --work-profile src/p95p98/profiles/reference.json \
     --resources resources/resources.json \
     --promod-python /path/to/promod-python \
     --cpu-seconds 1800 --wall-seconds 5400 \
     --output results/p95
   ```

4. For P98, use `--policy P98 --output results/p98`.

`--promod-python` points to a Python interpreter or wrapper that loads the compatible native ProMod3 environment. You don't need a reference structure, benchmark index, old result cache or LLM account.

The reference work profile holds operation prices we measured in the past. It is not calibrated for new inputs. Logical work, measured CPU and wall time are recorded separately. Changing the work profile can change what a program does, because its choices depend on the budget. Building resources is a separate one-time cost.

## Outputs

- `final.pdb`: the delivered structure. If a bounded operation fails to return a candidate, this is the retained (kept) state.
- `result.json`: final status, fixed energies and source geometry, action counts, CPU/wall/logical costs, which program ran and the final structure's identity.
- `endpoint.json.gz`: full-precision coordinates, source context and bindings.
- `route_steps/` and `actions/`: decisions, native receipts, diagnostics and kept outputs. Failed attempts stay in the cost record.

Status values: `COMPLETE` means normal delivery. `BUDGET_DELIVERY` means the budget ran out and a kept state was delivered. `ERROR` means execution failed; the last committed state is kept, but don't count it as a success.

`geometry_valid` refers to our existing source-geometry checks. It is not a clean MolProbity result. Running a program never loads reference RMSD or runs the development-set evaluator. If you repeat an identical request that already completed, it reuses the saved result. Incomplete requests are not replayed automatically.

## Tests and method boundaries

```sh
python -m unittest discover -s tests -v
```

[Validation results](docs/VALIDATION.md) keep software and interface tests separate from runs of the installed package with native tools. The [release checklist](docs/RELEASE_CHECKLIST.md) lists what's left before publication.

P95/P98 are byte-identical to the programs we evaluated. Any changes for installation or file paths live in the surrounding host. The programs choose among existing native KIC, packing, minimization, Monte Carlo and ProMod3 operations and control the callbacks those operations expose. See [provenance](PROVENANCE.json).

OpenEvolve, LLM calls and training/evaluation belong to program discovery, not to running P95/P98. This repo doesn't yet include a runnable reproduction of that search, but you can inspect the discovery ledger and real patch examples. BENCH48 is development evidence. The six-target CASP15 pilot adds limited outside evidence that stopping behavior depends on the starting model. Neither shows the programs work everywhere. Deployment CPU does not include the cost of discovering the programs.

## Versions, licenses and citation

We publish this release in a full fork of the official `RosettaCommons/rosetta` repository, with the upstream license and source kept. Our original harness and programs use the package's [MIT license](LICENSE). The Rosetta-derived scheduler is not covered by that license and keeps Rosetta's terms. See [native runtime and provenance](docs/NATIVE_RUNTIME.md). Native runtime wheels and separately installed databases keep their own terms. The package includes no binaries, accounts or SSH configuration.

If you use this code, report release 0.1.0, the policy hash, native runtime versions, resource and profile identities, and the execution budget. This release has no method paper or DOI yet. Cite the underlying [NGK work](https://doi.org/10.1371/journal.pone.0063090), [PyRosetta](https://doi.org/10.1093/bioinformatics/btq007) and [ProMod3](https://doi.org/10.1371/journal.pcbi.1008667) as applicable.
