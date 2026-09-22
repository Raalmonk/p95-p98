# Validation — 22 September 2026

## Software checks

54 focused tests passed both locally and against the installed Linux package:
policy identities, unchanged Router, source-only views,
memory/RNG commits, loop conversion, chemistry, accounting, failure retention,
ProMod resource exclusion and subprocess classification. These use software
fixtures; they are not 54 native structure computations.

The wheel was built and installed into a separate installation directory with
Python 3.12.3. The installed `p95p98` executable was invoked from outside the
source checkout. No experimental manifests, reference coordinates or old result
cache were available through the inference inputs. Dependencies were the
existing licensed PyRosetta build and separately installed ProMod3/OpenStructure
runtime. Both immutable policy hashes passed the installed identity check.

## Installed native example

One public input, PDB 1L2Y model 1 chain A, was run with each frozen program.
Loop 10–15, cut 12, local energy region 10–15, seed 20260922, `input_kind=W`,
reference work profile; limits were 1800 CPU seconds and 5400 wall seconds.
The server exposed 16 CPUs and 30 GiB memory. Each native action used one thread.

| Program | Status | Actual actions | CPU s | Wall s | Logical work |
| --- | --- | --- | ---: | ---: | ---: |
| P95 | COMPLETE | NGK refine → minimize | 109.838 | 142.009 | 365.442 |
| P98 | COMPLETE | NGK refine | 45.793 | 58.916 | 148.494 |

Both delivered full structures satisfying the fixed source-geometry check.
NGK policy callbacks, memory transfer, candidate serialization/restoration and
normal delivery ran through the installed package. All three actions returned
normally; there were no CPU/wall terminations or emergency deliveries. No LLM
calls or reference-structure scores were used. There were no completed native
action retries. A preceding wheel-build attempt lacked setuptools in the build
environment; isolated build dependency installation fixed this before modelling.

The [output PDBs and numerical receipt](../examples/outputs/summary.json) are
included. These are software verification outputs, not evidence that one program
is faster or more accurate in general. The README figure remains the separate,
previously completed BENCH48 comparison.

The example-specific source-excluded ProMod library contains 8632 coordinate
records, with coupled fragment lengths 3–14. Construction took 29.36 CPU seconds
and 30.86 wall seconds, outside inference. Native databases were built from
locally acquired upstream resources and are not included in the repository.

The policies did not request ProMod3 or NGK rebuild on this example. Their
branch-specific tests must not be described as policy-selected paths here.

One separate database adapter check on the same public input returned a complete
20-residue model: database fill (one gap → zero), sidechain reconstruction,
native minimization, final model check and exact mapped sequence coverage.
The PyRosetta host accepted its chemical identity without adaptation. This one
native invocation took 1.503623 CPU seconds and 1.8021404 wall seconds; separate
host initialization/loading/compatibility checking took 3.733267975 CPU seconds.
It used the existing example-specific library, with a 240 CPU/720 wall-second
software-test ceiling. It did not rerun either policy or score reference RMSD.
The Monte Carlo ProMod branch and NGK rebuild were not separately exercised in
this release smoke test.
