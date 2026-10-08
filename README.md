# LLM-guided algorithm discovery for computational biology

NGNGK uses OpenEvolve-guided program search to find decision rules for protein-loop modeling. A general-purpose LLM proposes programs that choose when to retrieve a candidate, sample a new structure or stop a calculation. We check and evaluate these programs on structure-modeling tasks, then run the selected programs without the LLM.

P95 and P98 are the frozen programs from proposals 95 and 98 in a search of approximately 100 candidates. They contain executable control rules; they are not protein foundation models.

[Research overview](p95-p98/docs/RESEARCH_OVERVIEW.md) · [Discovery records](p95-p98/docs/closeout/DISCOVERY.md) · [External results and traces](p95-p98/docs/closeout/casp15/INTERPRETATION.md) · [Install and run](p95-p98/README.md)

## Which calculations are worth doing?

A protein loop is a segment connecting other parts of a protein structure. Given its sequence and surrounding structure, a modeling tool can try different conformations, adjust sidechains and evaluate candidate energies. NGK is an established Rosetta procedure for this search; Monte Carlo sampling explores alternatives rather than accepting only immediately favorable changes.

Our question is how to control the search: when to retrieve a database candidate, when to sample, which structure to retain, and when more computation is unlikely to justify its cost. Running longer can lower modeled energy without moving closer to an experimental structure. The [results](p95-p98/docs/closeout/RESULTS.md) measure those outcomes separately.

```text
Researcher defines editable code, observations and evaluation
                            ↓
                 LLM proposes a control program
                            ↓
          Check code → run native tools → measure results
                            ↓
            Feed measurements into the next proposal
                            ↓
         Freeze selected programs → test on new inputs
                            ↓
         Deploy ordinary CPU code, with no LLM calls
```

[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) supplies the evolutionary program-search framework. Our contribution is the protein-modeling interface, source-only observations, native Monte Carlo controls, evaluation and evidence linking the discovered code to its behavior. The search changes the control program while keeping the LLM weights and protein energy function fixed.

## Results

### Combined routing and control on the development benchmark

The BENCH48 panel was used during discovery and selection. The programs could choose retrieval, rebuilding, refinement and lightweight minimization instead of applying the same long search everywhere.

| Program | Total logical work / native NGK | Geometry-valid outputs | Median local CA RMSD |
|---|---:|---:|---:|
| P95 | 16.11% | 48 / 48 | 0.820 Å |
| P98 | 25.13% | 48 / 48 | 0.780 Å |
| Native NGK | 100% | 47 / 48 | 0.878 Å |

Each program recorded 11 database calls, 37 NGK-refinement calls and two NGK-rebuild calls; actions can co-occur. The results measure the combined workflow. Retrieval's contribution was not measured separately. The 48 development inputs represent 32 homology components and were used during discovery and selection. Both programs had worse raw RMSD on the hard group; see the [complete report](p95-p98/docs/closeout/RESULTS.md).

Logical work measures the study's computation budget rather than elapsed seconds. The RMSD column uses the scaffold-fit CA display metric, distinct from the external test's local-backbone metric.

[![Development-set structure quality and recorded cost](p95-p98/docs/figures/method_comparison.png)](p95-p98/docs/figures/method_comparison.pdf)

[Figure definitions](p95-p98/docs/figures/CAPTION.md) · [144-row development data](p95-p98/docs/closeout/results/per_input.csv)

### Computational savings without a database call

A separate test used six new CASP15 targets, each with an existing AlphaFold2 and ESMFold prediction. The already-frozen programs received these structures directly, without compulsory NGK reconstruction. Neither program selected database retrieval in any run.

On the six AlphaFold2 starting models, P98 used 6.66% of native warm-start NGK's measured method CPU, with slightly lower mean local backbone RMSD: 1.602 versus 1.630 Å. The program stopped all six runs early inside NGK, after 0, 0, 13, 2, 0 and 27 KIC attempts. These counts confirm that the runs used less sampling.

| Starting models | P98 mean CPU | Native NGK mean CPU | P98 / NGK CPU | Untreated source RMSD | P98 RMSD | Native NGK RMSD |
|---|---:|---:|---:|---:|---:|---:|
| AlphaFold2, 6 targets | 14.45 s | 216.94 s | 6.66% | 1.596 Å | 1.602 Å | 1.630 Å |
| ESMFold, same 6 targets | 247.34 s | 163.26 s | 151.50% | 5.433 Å | 5.743 Å | 5.780 Å |
| All 12 inputs | 130.89 s | 190.10 s | 68.85% | 3.515 Å | 3.672 Å | 3.705 Å |

Both source-model conditions were specified before testing. On AlphaFold2 starts, P98 also used 29.83% of the fixed short-NGK control's CPU, with lower mean local RMSD (1.602 versus 1.817 Å). Because these runs made no database calls, the savings show that the discovered program can reduce native sampling costs through control decisions, particularly early stopping.

P98's mean local RMSD was 0.0053 Å higher than the original AlphaFold2 predictions, and its ESMFold runs cost more than full NGK. All four methods had higher pooled mean local RMSD than the untreated inputs. The [full comparison](p95-p98/docs/closeout/casp15/INTERPRETATION.md) retains P95, the short baseline, energies, every target and repair costs. It does not isolate a benefit from changing acceptance temperature.

The 48 method runs cover six target units with one algorithm seed. CPU includes the method host and observations but excludes upstream prediction, resource building and final evaluation. It is not a wall-clock speedup or BENCH48 logical work. All 48 outputs passed the existing geometry checks; MolProbity was skipped.

## What the search produced

The run recorded 101 model starts, 100 returned programs and 99 legal evaluated programs. P95 and P98 came from proposals 95 and 98. The run was a bounded proof of concept. It did not train neural-network weights or test whether a longer search would improve the programs.

The records link code proposals to their evaluations, the frozen programs and their decisions on new inputs. The records include successful edits, a rejected candidate and a missing-answer record. Human problem formulation, coding-assistant implementation and automated search are distinguished in the [discovery account](p95-p98/docs/closeout/DISCOVERY.md).

The study tests whether program search can turn scientific workflow heuristics into executable rules that can be inspected and evaluated. We used Rosetta as the testbed; transfer to other biomolecular workflows remains untested. The [research overview](p95-p98/docs/RESEARCH_OVERVIEW.md) explains the connection to OpenEvolve, AlphaEvolve and AI-assisted scientific computing, with an actual rule from the discovered program.

## Inspect without running protein models

From `p95-p98/`:

```sh
python3 docs/closeout/discovery/verify.py
python3 docs/closeout/results/summarize.py
python3 docs/closeout/casp15/summarize.py
```

These commands check retained records and reproduce summaries without LLM or Rosetta calls. [Evidence index](p95-p98/docs/closeout/EVIDENCE_INDEX.md) · [Native counters](p95-p98/docs/closeout/casp15/mc_control_counts.csv) · [Compact callback records](p95-p98/docs/closeout/casp15/mc_control_evidence.json). The [earlier General pilot](p95-p98/docs/closeout/GENERAL_PILOT.md) remains a separate, limited post-reconstruction comparison.

## Run the frozen programs

The package remains [`p95-p98/`](p95-p98/). It requires Linux Python 3.12, the pinned licensed PyRosetta build and a separate ProMod3 environment. No LLM account or OpenEvolve installation is required for deployment.

```sh
git clone --filter=blob:none --sparse --branch codex/p95-p98 https://github.com/Raalmonk/p95-p98.git p95p98-rosetta
cd p95p98-rosetta
git sparse-checkout set p95-p98
cd p95-p98
python -m pip install .
p95p98 verify
```

[Installation and inputs](p95-p98/README.md) · [Detailed method](p95-p98/docs/METHOD.md) · [Validation](p95-p98/docs/VALIDATION.md). The published release passed 54 software tests and completed the public 1L2Y installation example; those checks are separate from scientific evaluation. The repository provides discovery evidence, not a turnkey reproduction of the complete search.

## Attribution and licenses

We use OpenEvolve for program search. Rosetta supplies native physical operations; ProMod3 supplies retrieval and sampling. This full fork of [RosettaCommons/rosetta](https://github.com/RosettaCommons/rosetta) retains the original [Rosetta README](README.Rosetta.md) and [license](LICENSE.md). Original controller/harness code has its own [license](p95-p98/LICENSE), excluding the Rosetta-derived scheduler. Native and frozen policy code are unchanged. Runtime binaries and databases are not bundled.
