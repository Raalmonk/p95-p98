# P95 and P98 execution semantics

P95 and P98 are frozen decision programs. The host passes `event`, a source-only
`observation`, and trajectory-local `memory` to `decide(view)`. The returned
decision controls the next operation; returned memory carries across outer
routing and inner NGK callbacks. Deployment does not call an LLM.

Outer routing selects an available action and parent, retains outer state slots,
or delivers a state. Inner callbacks can stop the native trajectory and use
native acceptance or a 0.75 temperature multiplier. Both programs retain
`native_low` delivery. They do not use custom inner save/restore, direct
acceptance-probability overrides, or non-native KIC perturbations.

## State and observations

The host derives geometry, fixed energies, per-loop and per-residue information
from the supplied source and current candidates. Source displacement is measured
against the original supplied structure. Reference coordinates, reference RMSD,
benchmark labels, and offline evaluation results are absent from runtime views.
Observation construction must leave the native random stream unchanged.

Native loop definitions use one-based pose indices. Observation loop intervals
and residue indices use zero-based indices. The host must translate once and
check that both definitions identify the same residues. Fixed local energy is
the sum over the declared local energy region; the region is an explicit input
binding, not inferred from a target structure.

The frozen fixed score uses ref2015 with backbone hydrogen bonds decomposed into
pair energies. NGK's changing active score and the fixed observation score have
different roles and must remain separate in observations.

## Random stream and commit

Coordinates retained in an outer parent slot do not reset the current route
random stream. An operation starts from the chosen parent's coordinates and the
current route RNG. Successful operations commit their resulting coordinates,
RNG, and controlled-policy memory together. Native-low recovery follows the
native protocol; it is not an instruction to reset RNG to an earlier candidate.

On an uncommitted failed operation, the last committed endpoint remains
available and the failed attempt's measured cost remains recorded. Resume
requires an unambiguous retained operation state; an existing intent alone does
not establish either success or safe replay.

## Budgets

Recorded CPU, elapsed wall time, and calibrated logical work are separate
quantities. Original BENCH48 execution used input-specific logical tariffs,
physical CPU protection, action caps, and delivery reserves. A portable runtime
must identify its work profile in its output. Running the exact policy with a
different tariff does not reproduce the original budget-dependent trajectory.

A portable work profile should contain the four kernel prices (`kic`, `repack`,
`rotamer_trials`, `minimize`), observation/controller/archive/restore prices,
policy setup work, and their provenance. Original kernel prices equal measured
kernel CPU divided by operation count, multiplied by the ratio of net refinement
CPU to summed measured kernel CPU. Retaining an exact historical price profile
permits execution on a new source without reading benchmark inputs. The profile
must be named as a reference tariff rather than a calibration of the new input.
Do not replace missing prices with zero or arbitrary unit costs: both programs
use absolute work thresholds, and P95 also gates repeat descent by its measured
fraction of the original allowance.

## Native dependency

The native integration requires the legacy NGK callback interface used by the
host. A stock NGK call without the inner callbacks does not execute the full
policy. Runtime receipts should identify the native build, interface version,
score profile, policy hash, input/loop bindings, random seed, and budget profile.

## Small public example

PDB [1L2Y](https://www.rcsb.org/structure/1L2Y), model 1, chain A is a public
20-residue Trp-cage structure suitable for a small execution example. PDB archive
data are distributed under [CC0](https://www.rcsb.org/pages/usage-policy).
Use a declared internal loop and preserve the source/download identity. An
execution example demonstrates loading, routing and output production; it does
not require a target structure or reference-quality measurement.
