# Beyond retrieval: control of NGK Monte Carlo sampling

**The external pilot shows that P98's computational benefit is not restricted to database routing.** No database action was taken in any of the 24 P95/P98 runs. On the six AlphaFold2 starting models, the already-frozen P98 program used **6.66% of native warm-start NGK's measured method CPU**, with slightly lower mean local backbone RMSD. All six runs recorded a voluntary stop inside NGK refinement.

This is evidence for useful **LLM-discovered Monte Carlo control, particularly early stopping**, on new protein inputs. It is not a claim that the LLM learned a new KIC solver, energy function or Monte Carlo algorithm, or that P98 improves every starting structure.

## Two complementary kinds of evidence

[BENCH48](../RESULTS.md) evaluates the complete routing-and-control programs on 48 development inputs from 32 homology components. Each program recorded 11 database invocations, 37 NGK refinement invocations and two NGK rebuild invocations; minimization counts were 44 for P95 and 48 for P98. Actions can co-occur within a run. [Extracted coverage](../results/action_coverage.json) comes from the original proposal summaries, not a new experiment.

P95 and P98 used 16.11% and 25.13% of the matched NGK total logical work. Retrieval is an available inexpensive route, but these aggregate results do not isolate how much of the savings came from retrieval, stopping or other decisions. It would be inaccurate to describe the programs as simply returning a database result on most of BENCH48.

The CASP15 supplement asks a different, narrower question: **does a frozen program still save computation when retrieval is not selected?** The answer is yes on the AlphaFold2 stratum below, but not consistently on the ESMFold stratum. There was no retraining or policy selection on this supplement. P98 was designated the primary frozen candidate before the results; P95 and both source-model strata remain reported.

## External results, with the comparator named explicitly

Six targets (T1104, T1109, T1123, T1139, T1187, T1194), each with an author-provided AlphaFold2 and ESMFold prediction, were evaluated with four methods and one fixed seed, 20261007: 48 runs. Loops are 6–9 residues long. No common NGK reconstruction was required before the first policy decision. Baselines use the same input structures and native warm-start refinement, with five or one outer cycles.

| Starting models | Method | Mean method CPU (s) | CPU / native NGK | Mean local backbone RMSD (Å) |
|---|---|---:|---:|---:|
| AlphaFold2, n=6 | Unprocessed source | No additional modeling | — | 1.5963 |
| AlphaFold2, n=6 | P95 | 98.587 | 45.44% | 1.7548 |
| AlphaFold2, n=6 | **P98** | **14.448** | **6.66%** | **1.6016** |
| AlphaFold2, n=6 | Native warm-start NGK | 216.944 | 100% | 1.6297 |
| AlphaFold2, n=6 | Short warm-start NGK | 48.436 | 22.33% | 1.8174 |
| ESMFold, n=6 | Unprocessed source | No additional modeling | — | 5.4328 |
| ESMFold, n=6 | P95 | 191.199 | 117.11% | 5.7553 |
| ESMFold, n=6 | **P98** | **247.341** | **151.50%** | **5.7425** |
| ESMFold, n=6 | Native warm-start NGK | 163.264 | 100% | 5.7804 |
| ESMFold, n=6 | Short warm-start NGK | 34.712 | 21.26% | 5.6971 |
| All inputs, n=12 | Unprocessed source | No additional modeling | — | 3.5145 |
| All inputs, n=12 | P95 | 144.893 | 76.22% | 3.7551 |
| All inputs, n=12 | **P98** | **130.894** | **68.85%** | **3.6721** |
| All inputs, n=12 | Native warm-start NGK | 190.104 | 100% | 3.7050 |
| All inputs, n=12 | Short warm-start NGK | 41.574 | 21.87% | 3.7573 |

Ratios are ratios of total paired method CPU, not ratios of medians. The 6.66% result belongs to this AlphaFold2-input pilot; it is not a correction of the unsupported historical “8%” claim. BENCH48 logical-work fractions and CASP15 measured CPU fractions are different quantities and should not be compared as though they were the same unit.

Against full NGK, P98 had lower local RMSD on five of six AlphaFold2 inputs and higher local RMSD on one. Against the unprocessed AlphaFold2 sources, two improved, two were unchanged at reported precision and two worsened; the mean change was +0.0053 Å. P98 therefore reduces additional NGK computation while remaining close to the source's mean accuracy; **it has not demonstrated an average accuracy improvement over AlphaFold2 itself**. Energy results are not uniformly better than the controls; all energies and global RMSDs are retained in the [full report](REPORT.md).

ESMFold is an important limit, not a discarded subgroup. P98 cost 1.515 times full NGK, and its mean local RMSD was 0.310 Å above the source. Across both source-model strata, all four methods had higher mean local RMSD than leaving the sources unchanged. This does not support applying refinement indiscriminately to every predicted protein.

## The program actually stopped sampling

Terminal native counters, rather than elapsed time alone, show the behavior. On AlphaFold2 starts:

| Target | P98 KIC attempts | Voluntary native-stage stop | P98 CPU (s) | Native NGK CPU (s) |
|---|---:|---|---:|---:|
| T1104 | 0 | Yes | 8.723 | 91.857 |
| T1109 | 0 | Yes | 12.798 | 251.427 |
| T1123 | 13 | Yes | 25.173 | 334.972 |
| T1139 | 2 | Yes | 10.989 | 237.498 |
| T1187 | 0 | Yes | 11.464 | 242.887 |
| T1194 | 27 | Yes | 17.540 | 143.024 |

Zero KIC does not mean zero work: initialization, sidechain operations and, where selected, outer minimization still run. All six outcomes were normal deliveries, not timeouts. No reference RMSD or AlphaFold confidence was supplied to these stopping rules.

On ESMFold T1123 and T1139, P98 instead made 800 KIC attempts each without a recorded voluntary stop, with 4,433/4,437 controller calls and 7,208/7,116 observation-scoring calls. Their costs were 310.126/487.209 seconds versus 75.744/204.293 seconds for native NGK. These records suggest that continuing a long trajectory can expose substantial observation/control overhead; no profiling ablation quantifies each component's causal contribution.

The released policies also contain a conditional acceptance-temperature multiplier of 0.75. **This pilot does not isolate a benefit from that multiplier or establish an improved annealing schedule.** Callback samples are sparse, so they must not be mistaken for a complete temperature-override count. The direct mechanistic evidence here is recorded stopping and reduced KIC work; the quality comparison evaluates the whole frozen program, including its minimization and retention choices.

## Recompute and inspect

```sh
python3 docs/closeout/casp15/summarize.py
python3 docs/closeout/discovery/verify.py
```

Run from the package directory. The first command verifies the scalar/trace joins and recomputes the tables without executing Rosetta, an LLM or a policy. The second verifies the retained discovery chain. [48-row scalar data](results_per_input.csv), [24-policy native counters](mc_control_counts.csv), and [compact trace evidence](mc_control_evidence.json) retain exact source hashes. The trace file is an extraction from stored receipts, not a newly generated historical log.

The input source repositories are [Bhattacharya-Lab/CASP15](https://github.com/Bhattacharya-Lab/CASP15/tree/96687bc0f6e117240015766bb7c4d8b11ec796cd) and [KarmaLoop](https://github.com/karma211225/KarmaLoop/tree/962557be5d1efc9ff37dcd4f2002a4c534c44567/example/CASP15). Existing predictions were reused; no new AlphaFold/ESMFold inference was performed. Selection used target/loop metadata and an explicit sequence-exclusion screen against 896 recorded exclusion sequences, not endpoint quality. The global alignment rule was identity ≥30% with bidirectional aligned coverage ≥80%; it does not exclude all remote homology or unknown historical exposure.

Method CPU includes the policy host and observations, but excludes upstream prediction, one-time library construction and final evaluation. The [full report](REPORT.md) separately retains 156.183 seconds of prior record-order repair attempts, 148.440 seconds of resource building, preflight and evaluation costs. All 48 outputs passed the existing geometry checks; MolProbity was skipped, not passed. There are six independent target units and only one algorithm seed. The older General pilot remains a separate, explicitly limited experiment, not silently replaced by this panel.

## Measurement definition

The retained evaluator uses explicit sequence-to-reference correspondence. Local RMSD is measured on N/CA/C/O atoms in its loop-centered evaluation window after fitting the flanking N/CA/C anchors. Global CA RMSD has a separate fit over mapped CA atoms. Missing reference atoms are not filled from the prediction. Energies use the existing fixed ref2015 export, with loop-local and whole-pose sums. These definitions are not interchangeable with the BENCH48 scaffold-fit CA display metrics. No geometry, score or alignment definition changed for this publication.
