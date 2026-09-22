# P95 / P98

**LLM-discovered control programs for budgeted protein loop modeling.**

P95 and P98 use source-structure observations and search history to choose
native modeling operations, retain candidates and stop. Deployment runs on CPUs
without an LLM account or OpenEvolve installation.

[Installation and usage](p95-p98/README.md) ·
[Method](p95-p98/docs/METHOD.md) ·
[Validation](p95-p98/docs/VALIDATION.md) ·
[Source code](p95-p98/src/p95p98)

## Method

![Program discovery and the controlled NGK refinement loop](p95-p98/docs/figures/Training_Workflow_NGK.svg)

The frozen programs control routing, candidate retention, stopping and exposed
NGK callbacks. Native KIC closure, packing, minimization and Monte Carlo remain
provided by Rosetta. ProMod3 supplies native database and sampling operations.

## Computational time and structure quality

[![BENCH48 method comparison](p95-p98/docs/figures/method_comparison.png)](p95-p98/docs/figures/method_comparison.pdf)

[Vector PDF](p95-p98/docs/figures/method_comparison.pdf) ·
[Measurements and sample counts](p95-p98/docs/figures/CAPTION.md)

These are the completed BENCH48 development results, not an independent test
set. The two Agent pilots each contain three inputs. Recorded CPU excludes
program-discovery cost; the caption describes timing scope and method identities.

## Run

The installable package is in [`p95-p98/`](p95-p98/). It requires Linux Python
3.12, the pinned licensed PyRosetta build, and a separately configured ProMod3
environment. Dependency versions, source-excluded database construction and the
public input example are documented in the [installation guide](p95-p98/README.md).

```sh
git clone --filter=blob:none --sparse --branch codex/p95-p98 https://github.com/Raalmonk/p95-p98.git p95p98-rosetta
cd p95p98-rosetta
git sparse-checkout set p95-p98
cd p95-p98
python -m pip install .
p95p98 verify
```

Both installed policies completed the public 1L2Y example. The release also
passed 54 software tests and a native ProMod3 database/compatibility check.
[Actual example outputs and receipts](p95-p98/examples/outputs/summary.json)
are separate from the benchmark comparison above.

## Rosetta source and license

This is a full fork of [RosettaCommons/rosetta](https://github.com/RosettaCommons/rosetta).
The release branch starts at the compatible Rosetta commit
`5e498f1409c68ade56c8ce5842bf79e1b02e8db4`; its native source is unchanged.
The original [Rosetta README](README.Rosetta.md) and [license](LICENSE.md) are
retained. Original controller/harness code has its own
[license](p95-p98/LICENSE), which excludes the Rosetta-derived scheduler.
Runtime binaries and separately obtained databases are not bundled in the package.
