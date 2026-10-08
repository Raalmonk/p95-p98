# Native runtime and the Rosetta fork

We publish as a full fork of the official `RosettaCommons/rosetta` repository, at `Raalmonk/p95-p98`. The fork keeps Rosetta's upstream source and license. The `codex/p95-p98` release branch starts at the pinned commit below, and this package lives in its `p95-p98/` directory.

**Packaging this release does not need any patch to Rosetta's C++ or its native bindings.** Our Python host reproduces the legacy refinement schedule using standard PyRosetta interfaces:

- It calls the native KinematicMover, NeighborDependentTorsionSamplingKinematicPerturber, pack_rotamers, rotamer_trials, MinMover and MonteCarlo.
- The native LoopRelaxMover handles the first stage (rebuild and full-atom setup).
- The Python adapter supplies the policy callbacks.

## Set up the runtime

1. Use Python 3.12 on Linux x86-64.
2. Get this exact wheel through the licensed RosettaCommons PyRosetta distribution (it is not included in this package, and neither is its database):
   - PyRosetta `2026.03+releasequarterly.5e498f1409`
   - Rosetta commit `5e498f1409c68ade56c8ce5842bf79e1b02e8db4`
   - File `pyrosetta-2026.3+releasequarterly.5e498f1409-cp312-cp312-linux_x86_64.whl`
   - SHA-256 `5bf8ce053b0883bd301d286078d784869637d0f56e2de7f494c7dc4ab460edc0`
3. Install it with `python -m pip install PATH`.

The host checks the runtime version before it starts legacy refinement.

## Where the code came from

The scheduler comes from `mc_evolution/native_integration/legacy_refine.py`. Its native baseline is Rosetta's `LoopMover_Refine_KIC` at the commit above. The extracted copy keeps:

- the float32 temperature schedule
- the order of score ramping
- MoveMap behavior
- native RNG (random number generator) and acceptance
- the repack and minimization operations

The legacy refinement source is byte-identical, SHA-256 `59cb3073e0d7cc505248720e54d005be806aa0a090e3069266530653e9bb5855`.

Other modules:

| File | What it keeps or changes |
|---|---|
| `legacy_protocol.py`, `policy_adapter.py` | Keep the existing first-stage gate and callback wiring. The package-relative imports are changes made for deployment. |
| `observations.py` | Keeps the existing observation builder, which uses only the input structure. |
| `backend.py` | Takes only `RosettaBackend` from the saved HPC integration source (SHA-256 `24310ae261f9e21747a9321c700e7fda6ddd2c02dd5a56cbba452c155339483e`). |
| (geometry reduction) | Comes from `ws_preparation_numerics.py` (SHA-256 `69b35ca3e0fccea300587daac060acac88904e3043a74c4cbfd0915bb5fb882f`). Like the observation builder, it uses only the input structure. |
| `native/runtime.py` | Replaces the dataset-index constructor. It takes a prepared PDB, target sequence, explicit local energy region, loop definitions and seed. The existing observation and state methods stay, with package imports and direct input metadata. |
| `execution.py` | Keeps the evaluated policy-memory session and the refinement adapter that charges for observations. |
| `decision_trace.py` | Changes only import paths and the trace split label (to support `INFERENCE`). Callback sampling and recorded decisions are unchanged. |
| `observation_billing.py`, `budgeted_refinement.py` | Keep their behavior for charging operations and for cooperative stops on physical limits. |

The local energy region is a required input because the evaluated host did not always use only the loop.

We left out the reference evaluator, RMSD comparisons, the dataset loader, checkpoint machinery, and the experimental batch runners.

## Earlier qualification

The original qualification records show that the host and native code agreed exactly on endpoint, energy and RNG for three loop layouts: a single 12-residue loop, a single 16-residue loop, and two 8-residue loops. Those results are about the extracted scheduler. They are separate from checking this package's install and example.

## Licensing

The native scheduler is a transcription of Rosetta scheduling code. Do not present it as Rosetta relicensed under the harness license.

- Rosetta, PyRosetta and anything derived from upstream keep their upstream terms.
- The package's MIT license covers only the original harness and policies. It excludes `src/p95p98/native/legacy_refine.py`.
- The package bundles no native binaries or runtime databases. The surrounding fork keeps Rosetta's upstream source tree, including its database files.

## Scope

The decision not to patch Rosetta covers the P95/P98 chain we inspected. A future native callback implementation would need its own baseline and its own minimal patch review. Updating to upstream `main` is not part of this extraction.
