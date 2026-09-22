# Release checklist

Completed: standalone package/CLI, exact policies, source-only routing and native
callbacks, explicit input/resource/work-profile bindings, 54 software tests,
installed P95/P98 example outputs, a real ProMod database/chemical-compatibility
check, README figures and pinned dependency guides.
No Rosetta C++ or binding patch is required. See [validation](VALIDATION.md).

Publication is authorized in `Raalmonk/p95-p98`, a full fork of the official
`RosettaCommons/rosetta` repository. The release branch `codex/p95-p98` is rooted
at Rosetta commit `5e498f1409c68ade56c8ce5842bf79e1b02e8db4`, with this package
under `p95-p98/`. Upstream source and license are retained; the original harness
and policies are MIT-licensed, excluding the Rosetta-derived scheduler. The
repository homepage displays the release README and the supplied method figures.

The full OpenEvolve search/evaluator reproduction is not packaged. Runtime wheels
and external ProMod3 resources must be obtained separately. This packaging does
not change the runtime C++, frozen programs or scientific results.

## Verified implementation boundaries

- Frozen P95 and P98 bytes match `PROVENANCE.json`.
- An installed package resolves all internal modules without the experiment
  checkout, private absolute paths, or BENCH48 manifests.
- Native build and required callback symbols are pinned and checked before work.
- Runtime views contain only the source observation schema; no target loader or
  evaluator is on the execution path.
- Pose and observation loop indices identify the same residues; sequence,
  connections, score profile and local energy region are explicit bindings.
- Observation construction preserves RNG; selecting an older outer parent does
  not reset the current route RNG; commits include state, RNG and policy memory.
- Failed attempts remain in cumulative cost; CPU and logical work are distinct;
  work tariffs and delivery reserves are recorded.
- ProMod resource identity and configured executable are included in receipts;
  unavailable or failed database work returns a typed outcome rather than a
  fabricated candidate or silent replacement algorithm.
- Native operations run with bounded resources and a retained final endpoint;
  an interrupted operation is reconciled before any replay.
- A public small input includes download identity, explicit model/chain/loop,
  seed and demo budget. Execute the scoped smoke example remotely, without
  benchmark reruns or reference scoring, and retain command, exit and output.
- Package documentation distinguishes portable execution evidence from original
  BENCH48 results and does not relabel a new runtime profile as exact reproduction.
- The `p95-p98/` package contains intended source, documentation and example
  files, with dependency licenses preserved and no experiment/private resources;
  the surrounding fork retains the official Rosetta source.
