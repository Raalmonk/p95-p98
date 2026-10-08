# Earlier General pilot: separate, limited evidence

Before the direct-source CASP15 supplement, nine General proteins were tested with two seeds and four methods (72 planned positions). The pipeline first required a common native NGK reconstruction to return a complete starting structure. Only then did it call P95/P98 or the two warm-start NGK refinement controls. Failed or interrupted preparation was not an execution of any downstream policy.

The retained original snapshot contains 24 evaluated endpoints from three proteins (1B67, 1C0P and 1C4Q), six endpoints per method. Mean local RMSD was P95 2.4680 Å, P98 2.4787 Å, native NGK 3.0540 Å and short NGK 2.8295 Å. Mean standalone task CPU, charging the shared preparation once to each method task, was 332.196, 415.900, 299.519 and 129.377 seconds respectively. That task-cost convention is not total physical expenditure. The remaining positions had no prepared input in that snapshot; they remain in the planned denominator.

Subsequent budget-amended attempts and source-conversion repairs retained their original records and costs. The user ultimately stopped the remaining General work. No further modeling is implied by this publication. Preparation errors, genuine closure failures and user interruptions must not be combined into a single policy-failure rate.

This pilot supports only a conditional comparison of **refinement after successful common NGK reconstruction**. It does not test whether the router could avoid that reconstruction by choosing database retrieval. Its source-conversion problems and unusual hydrogen diagnostics also limit structural interpretation; incomplete MolProbity diagnostics were retained and further calls were skipped, not marked passed.

The [CASP15 supplement](casp15/INTERPRETATION.md) is a separately declared task on existing full predicted structures, without the common reconstruction gate. It is not a hidden replacement, a rerun of these nine proteins, or a reason to discard their less favorable costs and incomplete preparation coverage. The original General records remain archived separately from BENCH48 and CASP15.
