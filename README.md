# LLM-guided algorithm discovery for computational biology

**NGNGK: a case study in learning how to spend computation, not just predicting molecular structure.**

> Can a general-purpose language model discover an inspectable program that makes an existing scientific workflow more efficient?

This project uses **OpenEvolve-guided program search** to explore that question in protein-loop modeling. Rather than ask an LLM to invent protein coordinates or supervise every calculation, we let it propose changes to the **decision rules around established scientific operations**. Candidate programs are checked and evaluated on real structure-modeling tasks. The selected programs then run without the LLM.

**P95 and P98 are two frozen programs discovered in this study—not new protein foundation models.** Their names identify proposals from a limited search of approximately 100 candidate programs. The broader research object is how to discover and evaluate such executable rules.

[Research overview](p95-p98/docs/RESEARCH_OVERVIEW.md) · [Discovery records](p95-p98/docs/closeout/DISCOVERY.md) · [External results and traces](p95-p98/docs/closeout/casp15/INTERPRETATION.md) · [Install and run](p95-p98/README.md)

## The scientific question: which calculations are worth doing?

A protein loop is a segment connecting other parts of a protein structure. Given its sequence and surrounding structure, a modeling tool can try different conformations, adjust sidechains and evaluate candidate energies. NGK is an established Rosetta procedure for this search; Monte Carlo sampling explores alternatives rather than accepting only immediately favorable changes.

Our question is **how to control the search**: when to retrieve a database candidate, when to sample, which structure to retain, and when more computation is unlikely to justify its cost. Running longer can lower modeled energy without moving closer to an experimental structure. The [results](p95-p98/docs/closeout/RESULTS.md) measure those outcomes separately.

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

[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) supplies the evolutionary program-search framework. Our contribution is the protein-modeling interface, source-only observations, native Monte Carlo controls, evaluation and evidence linking the discovered code to its behavior. **The evolving object is the control program, not the LLM's weights or the protein energy function.**

## Two experiments, two complementary findings

### Combined routing and control on the development benchmark

The **BENCH48** panel was used during discovery and selection. The programs could choose retrieval, rebuilding, refinement and lightweight minimization instead of applying the same long search everywhere.

| Program | Total logical work / native NGK | Geometry-valid outputs | Median local CA RMSD |
|---|---:|---:|---:|
| P95 | **16.11%** | 48 / 48 | 0.820 Å |
| P98 | **25.13%** | 48 / 48 | 0.780 Å |
| Native NGK | 100% | 47 / 48 | 0.878 Å |

Each program recorded 11 database calls, 37 NGK-refinement calls and two NGK-rebuild calls; actions can co-occur. These results concern the **combined workflow**, not retrieval alone. The 48 inputs represent 32 homology components and are development data, not an independent test. Hard-group raw RMSD regressions remain in the [complete report](p95-p98/docs/closeout/RESULTS.md).

Logical work is the study's budget measure, **not seconds**. The RMSD column uses the scaffold-fit CA display metric, distinct from the external test's local-backbone metric.

[![Development-set structure quality and recorded cost](p95-p98/docs/figures/method_comparison.png)](p95-p98/docs/figures/method_comparison.pdf)

[Figure definitions](p95-p98/docs/figures/CAPTION.md) · [144-row development data](p95-p98/docs/closeout/results/per_input.csv)

### Computational savings without a database call

A separate test used **six new CASP15 targets**, each with an existing AlphaFold2 and ESMFold prediction. The already-frozen programs received these structures directly, without compulsory NGK reconstruction. Neither program selected database retrieval in any run.

**On the six AlphaFold2 starting models, P98 used 6.66% of native warm-start NGK's measured method CPU, with slightly lower mean local backbone RMSD: 1.602 versus 1.630 Å.** All six runs voluntarily stopped inside NGK. Their KIC attempts were **0, 0, 13, 2, 0 and 27**—direct evidence of reduced sampling, not a timing claim alone.

| Starting models | P98 mean CPU | Native NGK mean CPU | P98 / NGK CPU | Untreated source RMSD | P98 RMSD | Native NGK RMSD |
|---|---:|---:|---:|---:|---:|---:|
| **AlphaFold2, 6 targets** | **14.45 s** | 216.94 s | **6.66%** | 1.596 Å | **1.602 Å** | 1.630 Å |
| ESMFold, same 6 targets | 247.34 s | 163.26 s | 151.50% | 5.433 Å | 5.743 Å | 5.780 Å |
| All 12 inputs | 130.89 s | 190.10 s | 68.85% | 3.515 Å | 3.672 Å | 3.705 Å |

Both source-model conditions were specified before testing. On AlphaFold2 starts, P98 also used **29.83% of the fixed short-NGK control's CPU**, with lower mean local RMSD (1.602 versus 1.817 Å). This supports useful **LLM-discovered control of native sampling, particularly early stopping**, beyond choosing a cheaper database route.

The boundary is important: P98 did **not** improve average accuracy over the original AlphaFold2 predictions (+0.0053 Å mean local RMSD), and its ESMFold runs were more expensive than full NGK. All four methods had higher pooled mean local RMSD than the untreated inputs. The [full comparison](p95-p98/docs/closeout/casp15/INTERPRETATION.md) retains P95, the short baseline, energies, every target and repair costs. It does not isolate a benefit from changing acceptance temperature.

There are **six target units and one algorithm seed**: 48 method runs, not 48 independent proteins. CPU includes the method host and observations but excludes upstream prediction, resource building and final evaluation. It is not a wall-clock speedup or BENCH48 logical work. All 48 outputs passed the existing geometry checks; MolProbity was skipped.

## A limited search produced inspectable scientific decision rules

The run recorded **101 model starts, 100 returned programs and 99 legal evaluated programs**. P95 and P98 came from proposals 95 and 98. This is a bounded proof of concept, not an exhaustive search or neural-network training for 100 epochs; how much more search would help remains untested.

The evidence connects **real code proposals, evaluations, frozen programs and decisions on new inputs**. It includes successful edits, a rejected candidate and a missing-answer record. Human problem formulation, coding-assistant implementation and automated search are distinguished in the [discovery account](p95-p98/docs/closeout/DISCOVERY.md).

**The broader opportunity is to turn scientific workflow heuristics into executable, testable research objects.** Rosetta is the concrete testbed, not the limit of the research question. Transfer to other biomolecular workflows remains a direction to test. The [research overview](p95-p98/docs/RESEARCH_OVERVIEW.md) explains the connection to OpenEvolve, AlphaEvolve and AI-assisted scientific computing, with an actual rule from the discovered program.

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

OpenEvolve is existing search infrastructure, not an algorithm invented here. Rosetta supplies native physical operations; ProMod3 supplies retrieval and sampling. This full fork of [RosettaCommons/rosetta](https://github.com/RosettaCommons/rosetta) retains the original [Rosetta README](README.Rosetta.md) and [license](LICENSE.md). Original controller/harness code has its own [license](p95-p98/LICENSE), excluding the Rosetta-derived scheduler. Native and frozen policy code are unchanged. Runtime binaries and databases are not bundled.
