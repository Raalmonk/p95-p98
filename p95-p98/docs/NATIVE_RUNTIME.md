# Native runtime and Rosetta fork decision

The publication target is a full fork of the official `RosettaCommons/rosetta`
repository at `Raalmonk/p95-p98`, retaining upstream source and license. The
`codex/p95-p98` release branch is rooted at the pinned commit below; this package
lives in its `p95-p98/` directory. Publication packaging does not require a
Rosetta C++ or native binding patch. The existing Python host implements the legacy refinement schedule using
standard PyRosetta interfaces. It calls native KinematicMover,
NeighborDependentTorsionSamplingKinematicPerturber, pack_rotamers,
rotamer_trials, MinMover, and MonteCarlo. The native LoopRelaxMover supplies the
rebuild/full-atom prefix. The Python adapter supplies the policy callbacks.

The compatible runtime is PyRosetta `2026.03+releasequarterly.5e498f1409`,
Rosetta commit `5e498f1409c68ade56c8ce5842bf79e1b02e8db4`. The qualified wheel
is `pyrosetta-2026.3+releasequarterly.5e498f1409-cp312-cp312-linux_x86_64.whl`,
SHA-256 `5bf8ce053b0883bd301d286078d784869637d0f56e2de7f494c7dc4ab460edc0`.
Use Python 3.12 on Linux x86-64 and obtain this wheel through the licensed
RosettaCommons PyRosetta distribution. The wheel and its database are not in
this package. Install the obtained wheel with `python -m pip install PATH`.
The host checks the runtime version before entering legacy refinement.

The scheduler originates from `mc_evolution/native_integration/legacy_refine.py`;
its native baseline is Rosetta's `LoopMover_Refine_KIC` at the above commit.
The extraction preserves its float32 temperature schedule, score ramp ordering,
MoveMap behavior, native RNG/acceptance, repack and minimization operations.
`legacy_protocol.py` and `policy_adapter.py` preserve the existing prefix gate
and callback wiring. Package-relative imports are deployment adaptations.
`observations.py` retains the existing source-only observation builder.

`backend.py` extracts only `RosettaBackend` from the retained HPC integration
source snapshot (SHA-256
`24310ae261f9e21747a9321c700e7fda6ddd2c02dd5a56cbba452c155339483e`).
The source-only geometry reduction comes from `ws_preparation_numerics.py`
(SHA-256 `69b35ca3e0fccea300587daac060acac88904e3043a74c4cbfd0915bb5fb882f`).
The reference evaluator, RMSD comparisons, dataset loader, checkpoint machinery,
and experimental batch runners are excluded. `native/runtime.py` replaces the
dataset-index constructor with a prepared PDB, target sequence, explicit local
energy region, loop definitions and seed. The existing observation/state methods
are retained with package imports and direct input metadata. The local energy
region is required because the evaluated host did not always use only the loop.
The legacy refinement source itself is byte-identical, SHA-256
`59cb3073e0d7cc505248720e54d005be806aa0a090e3069266530653e9bb5855`.

`execution.py` retains the evaluated policy-memory session and observation-priced
refinement adapter. `decision_trace.py` changes only import paths and the trace
split label to support `INFERENCE`; its callback sampling and recorded decisions
remain unchanged. `observation_billing.py` and `budgeted_refinement.py` retain
their charged-operation and cooperative physical-stop behavior.

Original qualification records report exact host/native endpoint, energy and RNG
agreement on three loop topologies (single 12, single 16, dual 8+8 residues).
These historical qualifications concern the extracted scheduler and are separate
from the new package's installation and example verification.

The native scheduler is explicitly a transcription of Rosetta scheduling code.
It must not be represented as a relicensing of Rosetta under the harness license.
Rosetta/PyRosetta and any upstream-derived material retain applicable upstream
terms. The release retains the official upstream source and license in the fork;
the package's MIT license applies only to the original harness and policies and
excludes `src/p95p98/native/legacy_refine.py`. The package bundles no native
binaries or runtime databases. The surrounding fork retains Rosetta's upstream
source tree, including its database files.

This decision applies to the inspected P95/P98 chain. A future native callback
implementation would require its own baseline and minimal patch review; updating
to upstream `main` is not part of this extraction.
