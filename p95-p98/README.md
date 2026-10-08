# P95 / P98: executable controllers from LLM-guided program search

**The installable outputs of NGNGK, a case study in AI-assisted algorithm discovery for computational biology.**

Instead of asking an LLM to predict a protein structure, this study asks it to help discover **the rules that control a structure-modeling workflow**: which operation to try, which candidate to retain and when to stop spending computation. OpenEvolve-based search proposes and evaluates control programs; the selected programs then run independently of the LLM.

P95 and P98 are named for proposals 95 and 98 in a bounded run of approximately 100 candidates. They are ordinary, inspectable Python programs, not new neural-network models. The run recorded 101 model starts, 100 returned programs and 99 legal evaluated programs. No language-model weights were trained, and no claim of exhaustive search or convergence is made.

A Python host executes the frozen programs using source-structure observations, search history and a finite budget. Native Rosetta/NGK and ProMod3 supply the scientific operations. **No LLM account or OpenEvolve installation is needed for deployment.**

[Research idea and significance](docs/RESEARCH_OVERVIEW.md) · [How the programs were discovered](docs/closeout/DISCOVERY.md) · [Installation](#installation) · [Input format](#inputs)

## Method

![Program discovery, routing and the controlled NGK refinement loop](docs/figures/Training_Workflow_NGK.svg)

The searched rules control outer action selection, candidate retention and
history-dependent stopping. Within NGK, P95/P98 use native acceptance or a
conditional temperature multiplier of 0.75. KIC closure, structural moves,
sidechain operations and the native low-energy return are provided by the
underlying tools. The figure separates program discovery from deployment.

## Beyond retrieval: external Monte Carlo control

**On six external CASP15 AlphaFold2 starting models, P98 used 6.66% of native warm-start NGK's measured method CPU, with slightly lower mean local backbone RMSD (1.602 versus 1.630 Å), without a database call.** All six runs voluntarily stopped within NGK refinement; their KIC attempt counts were 0, 0, 13, 2, 0 and 27. This supports useful control of native Monte Carlo sampling, especially early stopping—not merely savings from retrieval.

| Starting models | P98 mean CPU | Native NGK mean CPU | P98 / NGK CPU | Source local RMSD | P98 local RMSD | NGK local RMSD |
|---|---:|---:|---:|---:|---:|---:|
| AlphaFold2, six targets | **14.45 s** | 216.94 s | **6.66%** | 1.596 Å | 1.602 Å | 1.630 Å |
| ESMFold, same six targets | 247.34 s | 163.26 s | 151.50% | 5.433 Å | 5.743 Å | 5.780 Å |
| All 12 inputs | 130.89 s | 190.10 s | 68.85% | 3.515 Å | 3.672 Å | 3.705 Å |

Both source-model strata and the primary P98 candidate were specified before the results. Four frozen methods and one seed give 48 runs, not 48 independent proteins. No common NGK reconstruction preceded policy decisions, and no database action was selected in any P95/P98 run. On AlphaFold2 starts P98 also used 29.83% of short-NGK CPU, with mean local RMSD 1.602 versus 1.817 Å.

The comparator is **additional NGK refinement**, not AlphaFold2 prediction itself: P98's mean local RMSD was 0.0053 Å above the unprocessed AlphaFold2 sources. ESMFold starts exposed higher costs, and every method's pooled mean local RMSD was worse than the untreated source. These results support conditional computational savings, not universal refinement, statistical equivalence or an isolated benefit from the 0.75 temperature multiplier. CPU and BENCH48 logical work are different units.

[Interpretation and all comparators](docs/closeout/casp15/INTERPRETATION.md) · [48-row results](docs/closeout/casp15/results_per_input.csv) · [Native MC counters](docs/closeout/casp15/mc_control_counts.csv) · [Recompute](docs/closeout/casp15/summarize.py)

## Development-set comparison

[![BENCH48 structural validity, recorded CPU and structural-quality distributions](docs/figures/method_comparison.png)](docs/figures/method_comparison.pdf)

[Vector PDF](docs/figures/method_comparison.pdf). The figure shows the existing
BENCH48 development results; Agent-Luna and Agent-Astra each have three inputs.
Recorded CPU describes deployment, not the preceding program-search cost.
Measurement definitions and sample counts are in the [figure caption](docs/figures/CAPTION.md).

### Recomputable development results

The same 48 inputs span 32 homology components and were used during program
discovery and selection. The following are recorded development results, not
an independent validation. RMSD medians use the common scaffold-fit CA display
definition; they are not the frozen dimensionless search objectives.

| Method | Valid / planned | Total logical work | Work / NGK | Accounted route CPU (s) | Median local CA RMSD (Å) | Median global CA RMSD (Å) |
|---|---:|---:|---:|---:|---:|---:|
| P95 | 48 / 48 | 8,518.318 | 16.11% | 9,974.949 | 0.820 | 0.226 |
| P98 | 48 / 48 | 13,285.407 | 25.13% | 14,903.911 | 0.780 | 0.225 |
| Native NGK | 47 / 48 | 52,864.757 | 100% | 55,905.890 | 0.878 | 0.267 |

Each program recorded 11 database invocations, 37 NGK-refinement invocations and two NGK-rebuild invocations across BENCH48; actions can co-occur. [Original action-coverage extracts](docs/closeout/results/action_coverage.json) show that this is a mixed routing-and-control benchmark, not mostly database returns. The exact share of savings attributable to retrieval was not isolated.

All methods returned 48 endpoints; the NGK invalid endpoint and all attempt
costs remain included. Accounted CPU preserves measured-cost reuse and excludes
final scoring, MolProbity, resource construction and LLM waiting. Logical work
is not seconds. The previously quoted **8% is not supported** for P95/P98 by
the audited cost summaries. Raw hard-group RMSD is worse for both programs;
the subgroup effects and all four raw quality metrics are in
[the results report](docs/closeout/RESULTS.md).

[Research evidence index](docs/closeout/EVIDENCE_INDEX.md) ·
[Discovery evidence](docs/closeout/DISCOVERY.md) ·
[144-row data and summary command](docs/closeout/results/TABLES.md) ·
[Earlier General pilot and its limits](docs/closeout/GENERAL_PILOT.md) ·
[CASP15 supplement results](docs/closeout/casp15/REPORT.md) ·
[External MC-control interpretation](docs/closeout/casp15/INTERPRETATION.md).

The CASP15 supplement above is separate from BENCH48 and the older General pilot. Its 48 outputs passed the existing geometry checks, but MolProbity was skipped. [The complete report](docs/closeout/casp15/REPORT.md) includes both frozen policies, both native controls, energies, global RMSDs and retained prior repair costs.

## Installation

Version **0.1.0** targets Linux x86-64 with Python 3.12. Install the licensed
PyRosetta `2026.03+releasequarterly.5e498f1409` wheel in that environment, then:

```sh
git clone --filter=blob:none --sparse --branch codex/p95-p98 https://github.com/Raalmonk/p95-p98.git p95p98-rosetta
cd p95p98-rosetta
git sparse-checkout set p95-p98
cd p95-p98
python -m pip install .
p95p98 verify
```

This repository is a full fork of `RosettaCommons/rosetta`; the commands
above check out only its `p95-p98/` package directory. With a full checkout,
enter `p95-p98/` from the repository root before installing.

The separate database/sampling worker uses ProMod3 3.7.0 and OpenStructure
2.12.0. Its Python environment may differ from PyRosetta's. Follow
[native runtime installation](docs/NATIVE_RUNTIME.md) and
[ProMod3 installation and resource construction](docs/PROMOD3.md) to obtain
the compatible dependencies and build a source-excluded fragment library.
All branches require these dependencies; the host does not silently substitute
another method when one is missing. No Rosetta C++ or native binding patch is
required to run the package.

## Inputs

Supply a complete, canonical protein PDB and the corresponding target sequence.
This release controls local search on **prepared structures**; it does not insert
new residues into an incomplete PDB. Indel candidates must first be converted
into a complete structure with the target sequence.

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

PDB paths are relative to the JSON file. Residue indices are one-based pose
indices, not PDB residue numbers. Loops are non-overlapping internal intervals
of at least three residues. Declare the local energy region explicitly, including
every loop residue. `input_kind` is the source provenance (`W`, `S`, or `hard`),
not a requested output quality. See [execution semantics](docs/METHOD.md).
Noncanonical residues, alternate conformers, insertion codes, disulfide-tagged
inputs and terminal loops are outside the prepared-input converter's scope.

## Run a public example

Download the pinned public structure:

```sh
python examples/fetch_1l2y.py --output examples/1l2y_model1_A.pdb
```

Build the resource library using `examples/protected.json` as described in
[the ProMod3 guide](docs/PROMOD3.md), then run:

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

Use `--policy P98 --output results/p98` for the other frozen program.
`--promod-python` names an interpreter or wrapper that loads the compatible
native ProMod3 environment. No reference structure, benchmark index, old result
cache or LLM account is required.

The explicit reference work profile retains measured historical operation
prices. It is not a new-input calibration. Logical work, measured CPU and wall
time are recorded separately; changing a work profile can change a policy's
budget-dependent trajectory. Resource construction is a separate one-time cost.

## Outputs

- `final.pdb`: the delivered structure, including retained-state delivery after
  a bounded operation fails to return a candidate.
- `result.json`: terminal status, fixed energies/source geometry, action counts,
  CPU/wall/logical costs, policy identity and final structure identity.
- `endpoint.json.gz`: full-precision coordinates, source context and bindings.
- `route_steps/` and `actions/`: decisions, native receipts, diagnostics and
  retained outputs. Failed attempts remain in the cost record.

`COMPLETE` means normal program delivery. `BUDGET_DELIVERY` means a retained
state was delivered when the budget closed. `ERROR` preserves the last committed
state and reports an execution failure; it must not be counted as a successful
run. `geometry_valid` describes the existing source-geometry checks, not a
MolProbity-all-clear certificate. Inference does not load reference RMSD or run
the development-set evaluator. Repeating a completed identical request reuses
its terminal record; incomplete requests are not automatically replayed.

## Tests and method boundaries

```sh
python -m unittest discover -s tests -v
```

[Validation results](docs/VALIDATION.md) separate software/interface tests from
installed-package native execution. [Release checklist](docs/RELEASE_CHECKLIST.md)
records the remaining publication items. P95/P98 are byte-identical to the
evaluated programs; installation/path adaptation is in the surrounding host.
The native KIC, packing, minimization, Monte Carlo and ProMod3 operations are
not newly learned algorithms. The programs select their use and control the
exposed callbacks. See [provenance](PROVENANCE.json).

OpenEvolve, LLM calls and training/evaluation belong to **program discovery**,
not deployment. This repository does not yet package an executable reproduction
of that search. The discovery ledger and real patch examples are provided for inspection. BENCH48 is development evidence; the separate six-target CASP15 pilot supplies limited external evidence for source-dependent stopping behavior. Neither study establishes universal generalization. Deployment CPU excludes the preceding algorithm-discovery cost.

## Versions, licenses and citation

The release is published in a full fork of the official
`RosettaCommons/rosetta` repository, retaining the upstream license and source.
The original harness and policies use the package's [MIT license](LICENSE);
the Rosetta-derived scheduler is excluded from that license and retains
Rosetta terms. See [native runtime and provenance](docs/NATIVE_RUNTIME.md).
Native runtime wheels and separately installed databases retain their own terms;
the package includes no binaries, accounts or SSH configuration.

When using this code, report release 0.1.0, policy hash, native runtime versions,
resource/profile identities and the execution budget. No method paper or DOI
has been assigned to this release. Cite the underlying
[NGK work](https://doi.org/10.1371/journal.pone.0063090),
[PyRosetta](https://doi.org/10.1093/bioinformatics/btq007), and
[ProMod3](https://doi.org/10.1371/journal.pcbi.1008667) as applicable.
