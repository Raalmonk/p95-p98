# Validation (22 September 2026)

We checked that the package installs and that both frozen programs run end to end on a small public protein. This is a software check, not a performance comparison.

## Software tests

54 focused tests passed, both locally and against the installed Linux package. They cover:

- policy identities
- the unchanged Router
- views built only from the input structure
- memory and RNG (random number generator) commits
- loop index conversion
- chemistry
- cost accounting
- keeping failed attempts on record
- excluding the input from ProMod resources
- classifying subprocess outcomes

These tests use software fixtures. They are not 54 native structure calculations.

## Install check

- We built the wheel and installed it into a separate directory with Python 3.12.3.
- We ran the installed `p95p98` executable from outside the source checkout.
- The inference inputs gave no access to experimental manifests, reference coordinates, or old result caches.
- Dependencies were our existing licensed PyRosetta build and a separately installed ProMod3/OpenStructure runtime.
- Both policy hashes passed the installed identity check.

One snag: the first wheel build failed because the build environment lacked setuptools. Installing build dependencies in isolation fixed it before any modeling.

## Running the example

We ran each frozen program once on PDB 1L2Y, model 1, chain A, with these settings:

| Setting | Value |
|---|---|
| Loop | 10–15 |
| Cut point | 12 |
| Local energy region | 10–15 |
| Seed | 20260922 |
| Input kind | `input_kind=W` |
| Work profile | reference |
| Limits | 1800 CPU seconds, 5400 wall seconds |
| Machine | 16 CPUs, 30 GiB memory; one thread per native action |

| Program | Status | Actual actions | CPU s | Wall s | Logical work |
| --- | --- | --- | ---: | ---: | ---: |
| P95 | COMPLETE | NGK refine → minimize | 109.838 | 142.009 | 365.442 |
| P98 | COMPLETE | NGK refine | 45.793 | 58.916 | 148.494 |

NGK is Rosetta's next-generation KIC loop modeling.

Both programs delivered full structures that passed the fixed input-geometry check. Through the installed package, we exercised:

- NGK policy callbacks
- passing memory between steps
- saving and restoring candidates
- normal delivery

All three actions returned normally. Nothing hit the CPU or wall limit, there were no emergency deliveries, and no native action was retried to completion. We made no LLM calls and used no reference-structure scores.

The [output PDBs and numerical receipt](../examples/outputs/summary.json) are included.

**These outputs verify that the software runs. They do not show that one program is faster or more accurate in general.** The README figure is a separate, earlier BENCH48 comparison.

## ProMod library for the example

We built a ProMod library for this example that excludes the input. It has 8632 coordinate records and coupled fragment lengths 3–14. Building it took 29.36 CPU seconds and 30.86 wall seconds, outside of inference. We built the native databases from upstream resources obtained locally; they are not in the repository.

Neither policy chose ProMod3 or an NGK rebuild on this example. Their branch-specific tests must not be described as paths the policies selected here.

## Separate database adapter check

We ran the ProMod database adapter once on the same input. It returned a complete 20-residue model:

1. Database fill (one gap down to zero).
2. Sidechain reconstruction.
3. Native minimization.
4. Final model check, with exact mapped sequence coverage.

The PyRosetta host accepted the model's chemistry without changes.

| Step | CPU s | Wall s |
|---|---:|---:|
| ProMod invocation | 1.503623 | 1.8021404 |
| Host setup, loading and compatibility check | 3.733267975 | not reported |

This check used the example-specific library and a software-test ceiling of 240 CPU seconds and 720 wall seconds. It did not rerun either policy or score RMSD against a reference.

Not run separately in this release check: the Monte Carlo ProMod branch and NGK rebuild.
