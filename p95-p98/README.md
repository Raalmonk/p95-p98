# P95 / P98

Frozen, LLM-discovered control programs for CPU-based local protein-structure
search. A Python host executes the selected program using source-structure
observations, search history and a finite budget. No LLM account or OpenEvolve
installation is needed for inference.

## Method

![Program discovery, routing and the controlled NGK refinement loop](docs/figures/Training_Workflow_NGK.svg)

The searched rules control outer action selection, candidate retention and
history-dependent stopping. Within NGK, P95/P98 use native acceptance or a
conditional temperature multiplier of 0.75. KIC closure, structural moves,
sidechain operations and the native low-energy return are provided by the
underlying tools. The figure separates program discovery from deployment.

## Development-set comparison

[![BENCH48 structural validity, recorded CPU and structural-quality distributions](docs/figures/method_comparison.png)](docs/figures/method_comparison.pdf)

[Vector PDF](docs/figures/method_comparison.pdf). The figure shows the existing
BENCH48 development results; Agent-Luna and Agent-Astra each have three inputs.
Recorded CPU describes deployment, not the preceding program-search cost.
Measurement definitions and sample counts are in the [figure caption](docs/figures/CAPTION.md).

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
of that search. The homepage comparison reuses the completed development study,
not the small installation example, and does not measure independent
generalization. Deployment CPU excludes the preceding algorithm-discovery cost.

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
