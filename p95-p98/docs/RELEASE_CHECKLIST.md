# Release checklist

## Done

- [x] Standalone package and CLI
- [x] Exact frozen policies
- [x] Routing that sees only the input structure, plus native callbacks
- [x] Explicit bindings for input, resources and work profile
- [x] 54 software tests
- [x] Example outputs for P95 and P98 from the installed package
- [x] A real check of the ProMod database and chemical compatibility
- [x] README figures and pinned dependency guides

No patch to Rosetta's C++ or bindings is needed. Details are in [validation](VALIDATION.md).

## Where it is published

Publication is authorized in `Raalmonk/p95-p98`, a full fork of the official `RosettaCommons/rosetta` repository.

- The release branch `codex/p95-p98` starts at Rosetta commit `5e498f1409c68ade56c8ce5842bf79e1b02e8db4`.
- This package is under `p95-p98/`.
- Upstream source and license are kept. The original harness and policies are MIT-licensed; the scheduler derived from Rosetta is excluded from that license.
- The repository homepage shows the release README and the method figures.

## Not included

- The full OpenEvolve search and evaluator reproduction.
- Runtime wheels and external ProMod3 resources. Get these separately.

This packaging does not change the runtime C++, the frozen programs, or the scientific results.

## Verified boundaries

- [x] The frozen P95 and P98 bytes match `PROVENANCE.json`.
- [x] The installed package finds all its internal modules without the experiment checkout, private absolute paths, or BENCH48 manifests.
- [x] The native build and the required callback symbols are pinned and checked before any work starts.
- [x] Runtime views contain only the input-structure observation schema. No target loader or evaluator is on the execution path.
- [x] Pose loop indices and observation loop indices point to the same residues. Sequence, connections, score profile and local energy region are explicit inputs.
- [x] Building observations does not change the random number generator (RNG). Choosing an older outer parent does not reset the current route's RNG. Each commit saves state, RNG and policy memory together.
- [x] Failed attempts still count toward total cost. CPU time and logical work are tracked separately. Work tariffs and delivery reserves are recorded.
- [x] Receipts include the ProMod resource identity and the configured executable. If database work is unavailable or fails, the result is a typed outcome, never a made-up candidate or a silent switch to another algorithm.
- [x] Native operations run with resource limits and keep their final endpoint. An interrupted operation is reconciled before any replay.
- [x] A small public input comes with its download identity, explicit model, chain and loop, seed, and demo budget. The scoped smoke example was run remotely, without benchmark reruns or reference scoring, and the command, exit status and output were kept.
- [x] The package docs separate portable execution evidence from the original BENCH48 results, and never call a new runtime profile an exact reproduction.
- [x] The `p95-p98/` package contains only intended source, docs and example files, keeps dependency licenses, and has no experiment or private resources. The surrounding fork keeps the official Rosetta source.
