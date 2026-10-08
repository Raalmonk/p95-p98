# Results: BENCH48 development data

P95 and P98 used **16.11% and 25.13% of native NGK's total recorded logical work**, respectively, on the same 48 development inputs. They delivered 48 valid endpoints each; NGK delivered 47. The frozen component-balanced objectives and raw subgroup results show a tradeoff: P98 improved all five objectives, but both programs had worse hard-group raw RMSD. This panel was used during program discovery and selection.

The prior “8%” statement is withdrawn: no verified 8% result was found in the retained P95/P98 versus NGK cost totals, per-input ratio medians, or ratios of median costs. P98's verified total-work reduction is 74.87%, not an 8% speed improvement.

## Numerical tables and reproduction

[TABLES.md](results/TABLES.md) gives the main raw means, three distinct cost ratios, and paired valid subgroup changes. [per_input.csv](results/per_input.csv) contains all 144 method–input rows, including the invalid NGK endpoint, original raw values, separate existing scaffold-fit display RMSDs, CPU components, wall time, and terminal identities. All four frozen raw quality metrics are available on 48/48 rows per method; valid pair counts versus NGK are 47 overall, 32 W/S and 15 hard. There are 32 homology components, not 48 independent proteins: W/S comprise 32 starts from 16 components, plus 16 hard components.

Run from the release root with Python's standard library; this reads only the shipped scalar CSV and regenerates the tables and machine-readable summary:

```sh
python3 docs/closeout/results/summarize.py
```

The project-private `artifacts/NGNGK_CLOSEOUT/results/extract_retained.py` extracts these scalars from the retained figure CSV, checks each input and terminal hash against the original manifest, and checks all original domain means and logical/route CPU totals against the final reports. [provenance.json](results/provenance.json) records those source identities. It does not reopen remote endpoint files or recompute coordinates. Original full terminal locators and hashes remain in the CSV without host/account paths.

## Frozen primary objectives

These are the original transformed, component-balanced, dimensionless objectives, all higher-is-better. They are preserved in [frozen_axes.csv](results/frozen_axes.csv), separately from the new descriptive arithmetic in the main table. No five-axis average or new winner is introduced.

| Method | Local RMSD axis | Global RMSD axis | Local energy axis | Global energy axis | Efficiency axis |
|---|---:|---:|---:|---:|---:|
| P95 | 0.518163 | 0.500362 | 0.518219 | 0.438657 | 0.878308 |
| P98 | 0.499389 | 0.490022 | 0.547624 | 0.465248 | 0.824536 |
| NGK | 0.465555 | 0.460504 | 0.467521 | 0.461339 | 0.317161 |

P95's global-energy objective is below NGK. For both programs the paired valid hard-group local/global RMSD changes are positive (worse). The raw all-input NGK energy means include its extreme geometry-invalid endpoint; the both-valid subgroup table exposes the paired energy regressions that a pooled mean can obscure.

NGK row36 returned a geometry-invalid endpoint after a CPU_LIMIT action; row35 also had a CPU_LIMIT action but returned a valid endpoint. Both costs and outputs remain included. P95/P98 have no endpoint failures in this panel. All three methods completed the 15-component MolProbity diagnostic collection on all 48 inputs; collection completion is not an anomaly-free result.

## Cost boundaries

| Method | Retained measured route CPU (s) | Reused preparation (s) | Accounted route CPU (s) | Final quality receipt CPU (s) | MP receipt CPU (s) | Sum active wall (s) | Sum worker wait (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| P95 | 9960.670 | 14.279 | 9974.949 | 7.537 | 5.439 | 9619.366 | 692.649 |
| P98 | 14889.631 | 14.279 | 14903.911 | 7.281 | 1.289 | 14525.217 | 130.638 |
| NGK | 55891.610 | 14.279 | 55905.890 | 7.025 | 1776.579 | 55316.972 | 6162.233 |

Each column has 48 measured/recorded rows per method. Accounted route CPU is retained measured route CPU plus exact measured preparation reused at rows17 and35; it includes retained failed attempts. NGK reused 46 whole routes, preserving their original CPU. Its `incremental_run_cpu_seconds` sums to 3520.462 s, whereas P95/P98 sum to 9960.670/14889.631 s in their original passes. Those incremental fields describe different historical execution passes and are not a matched speed ratio or this closeout's new CPU consumption. This closeout performed no structure computation.

The MP columns are recorded evaluation/retrieval costs, including reuse; they do not measure fresh full MolProbity execution for every endpoint. [evaluation_costs.csv](results/evaluation_costs.csv) preserves the report fields and measured-row counts. Neither final scoring nor MP is included in the route CPU comparison. Per-input active wall and queue wait are retained separately; summing overlapping input walls does not yield batch elapsed time. Timings were historical, not a controlled hardware speedup experiment. Logical work retains the original hybrid tariff definition; it is neither CPU seconds nor the new draft clock-independent action-price mode.

Discovery costs are distinct from deployment: all proposal evaluations recorded 380.437 route CPU hours, of which 372.876 hours were additional to P1; the three strong controls recorded another 19.631 hours. The 100 returned-program evaluation summaries separately sum to 761.163 s final-quality CPU and 32915.071 s MP receipt CPU, including the invalid-policy fallback and reuse. These are evaluation accounts, not reconciled new server consumption. The 100 known usage receipts contain 21,531,286 tokens; P96 usage is missing. The search used the existing subscription channel and recorded zero paid API calls. A reconciled discovery LLM-wait total, one-time resource-building total, and currency bill are unavailable in the selected closeout records and remain null in [discovery_costs.json](results/discovery_costs.json). No one-time costs or model wait are folded into route CPU.

## Metric definitions

The CSV's `legacy_local_rmsd_A` / `legacy_global_rmsd_A` are the frozen raw quantities. For W/S they use N, CA, C and O backbone atoms: prediction and reference are fitted independently to the same visible-source scaffold anchors, followed by local/global errors with no additional fit. Local covers the frozen expanded region L; global covers all final-sequence residues. For hard inputs they use CA atoms with explicit residue correspondence, independently fitting prediction and reference to fixed RAW source non-loop anchors; local covers the loop union and global all mapped residues. Pairing uses input index, episode and homology component, never nearest numerical value.

The pooled legacy RMSD means combine these two atom/region definitions and are included only for arithmetic traceability. Use the group-specific paired changes to describe frozen raw quality; use the explicitly labeled common CA display metric for a cross-domain geometric headline.

The existing figure's `local_rmsd_A` / `global_rmsd_A` are different derived display metrics: a single direct prediction-to-reference Kabsch fit on all mapped non-loop CA atoms, then loop-union/all-mapped CA RMSDs under that same transform. They are copied unchanged for figure reconciliation and do not replace the frozen objectives.

Both energies use the fixed ref2015 score with backbone hydrogen-bond pair decomposition, in REU. Local sums weighted per-residue contributions over the frozen local region (expanded L for W/S, loop union for hard); global covers the complete pose. CSV residue counts retain these boundaries. Geometry validity uses the fixed sequence, heavy-atom, chemistry/connectivity and geometry checks; low RMSD, low energy, and completed MolProbity diagnostics are separate observations.

## Fixed CASP15 direct-source supplement — 8 October 2026

**Additional interpretation: this test also separates MC control from retrieval.** No database action was selected. On the six AlphaFold2 starting models, frozen P98 used 6.66% of native warm-start NGK CPU (14.448 versus 216.944 seconds/input), with mean local backbone RMSD 1.6016 versus 1.6297 Å. All six native refinement receipts contain a voluntary stop. This is evidence of useful non-retrieval sampling control, not proof that a new MC algorithm or improved annealing schedule was learned.

The AlphaFold2 source mean was 1.5963 Å; average improvement over the source is not claimed. ESMFold starts did not preserve the compute advantage (151.50% of NGK CPU). [Full source-stratified interpretation, native counters and limitations](casp15/INTERPRETATION.md) complement, rather than replace, the pooled table below.


This separate input protocol uses six proteins, each with an existing AlphaFold2
and ESMFold prediction: 12 inputs × four methods × one fixed seed20261007 =48
positions. All48 returned endpoints satisfy the retained geometry-valid flag;
MolProbity was skipped. There is no shared NGK reconstruction prefix. These are
six proteins, not12 independent proteins, and this is not a replacement for the
old nine-protein General experiment or the BENCH48 tables above.

| Method | Geometry-valid / planned | Mean method CPU (s) | Mean local backbone RMSD (Å) |
|---|---:|---:|---:|
| P95 | 12 / 12 | 144.893 | 3.755 |
| P98 | 12 / 12 | 130.894 | 3.672 |
| native_NGK | 12 / 12 | 190.104 | 3.705 |
| short_NGK | 12 / 12 | 41.574 | 3.757 |

The unprocessed sources average3.514533Å local RMSD, lower than every method's
pooled mean. P95/P98 use less mean method CPU than native_NGK and more than
short_NGK; this does not establish superiority to leaving the predictions
unchanged. Both policies recorded12 ngk_refine and10 minimize actions; no
database action was recorded, so this panel does not test a retrieval-repair
advantage. All source-model strata and protein-level effects remain visible.

The table uses successful current-attempt outer method CPU. Original record-order
repair attempts add156.182618CPU seconds, retained separately by method;
resource build148.439991CPU seconds is counted once. Preflight and source/endpoint
evaluation are separate from method CPU. See the exact retained
[48-row CSV](casp15/results_per_input.csv) and [report](casp15/REPORT.md) for
mean/median/total costs, prior/cumulative costs, global RMSD, both energies,
paired source changes and separate AlphaFold2/ESMFold summaries.
