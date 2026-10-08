# Earlier General pilot: separate and limited

**This was an earlier, incomplete test. Only 3 of 9 proteins have results in the saved snapshot, so read it as a narrow side result.**

## What we planned

Before the CASP15 test, we planned to test nine "General" proteins with two seeds and four methods: 72 runs in all. Each run had two stages:

1. Rebuild the loop with native NGK (Rosetta's standard loop-modeling method) to get a complete starting structure. This step was shared by all four methods.
2. Only if that worked, run P95, P98, or one of the two NGK refinement baselines (native and short) on that structure.

If stage 1 failed or was interrupted, no method ran. Those cases are not failures of any of the four methods.

## What we got

The saved original snapshot has 24 finished runs from three proteins (1B67, 1C0P and 1C4Q), six per method. In that snapshot, the other planned runs had no prepared input. They still count in the planned total of 72.

| Method | Mean local RMSD (Å) | Mean standalone task CPU (s) |
|---|---:|---:|
| P95 | 2.4680 | 332.196 |
| P98 | 2.4787 | 415.900 |
| Native NGK | 3.0540 | 299.519 |
| Short NGK | 2.8295 | 129.377 |

RMSD measures distance from the real structure; lower is better. The CPU column charges the full shared stage-1 cost to each method's task. This is a per-task accounting choice. It is not the total CPU time we actually spent.

## What happened next

Later attempts, run with an amended budget, and repairs to source-file conversion kept their own original records and costs. The user eventually stopped the remaining General work. This write-up does not imply any further modeling. Setup errors, real loop-closure failures and user interruptions are different things. Don't lump them into one "policy failure rate".

## What this pilot shows, and doesn't

- It only compares refinement methods after the shared NGK rebuild succeeded.
- It does not test whether the program could skip that rebuild by choosing a database lookup instead.
- Problems converting source files, and unusual hydrogen diagnostics, limit what the structures can tell us.
- MolProbity diagnostics were incomplete. We kept what we had and skipped further calls. The skipped calls were not marked as passed.

## How it relates to CASP15

The [CASP15 supplement](casp15/INTERPRETATION.md) is a separate, declared test. It starts from complete existing predicted structures, so it has no shared rebuild step. It is not a quiet replacement for this pilot or a rerun of these nine proteins. It is also not a reason to drop this pilot's less favorable costs or its incomplete coverage. The General records stay archived separately from BENCH48 and CASP15.
