# From AI-written code to testable scientific algorithms

## The idea in one minute

Most immediately visible uses of AI in molecular research produce a prediction: a sequence, a structure, a binding score. This project explores a different output: **a program that decides how a scientific computation should proceed**.

A researcher defines what can change and how candidates will be evaluated. A language model proposes executable changes. Those programs are checked, run and compared, and their measured results guide further proposals. The final product is ordinary code that can be inspected and used without calling the language model again.

**NGNGK is a concrete protein-modeling case study of this approach.** Its released artifacts, P95 and P98, control existing operations rather than replace protein physics. A small external test found substantial computation savings in one starting-model condition without using database retrieval. The same test exposed another condition where the advantage did not hold. That combination makes both the possibility and the boundary of learned scientific control visible.

[Main results](../README.md#beyond-retrieval-external-monte-carlo-control) · [Discovery evidence](closeout/DISCOVERY.md) · [Complete external interpretation](closeout/casp15/INTERPRETATION.md)

## 1. Two searches at different levels

There are two distinct searches in this study.

**The structure search** explores molecular conformations. The sequence and surrounding structure are given; the modeling software tries changes to a specified loop, handles sidechains and scores the resulting structures. NGK—next-generation kinematic closure—provides established Rosetta machinery for this task. KIC solves geometric closure problems within that machinery. Monte Carlo acceptance permits exploration instead of always taking the immediately lowest-energy move. [Native method and provenance](METHOD.md).

**The program search** explores how to control those calculations. An LLM edits a Python decision function: choose an available operation, inspect current measurements and search history, retain a candidate, continue or stop. The host—not the editable function—owns the input, physical operations, resource identities and evaluation definitions. [Actual editable boundary](closeout/DISCOVERY.md#task-contributions-and-boundaries).

The second search is not merely a faster implementation of the first. It can change **which calculations are performed**, so its output need not be identical to a long, fixed protocol. That requires evaluation of both computation and structural quality. A cheaper trajectory is useful only within an acceptable quality tradeoff; passing software tests alone cannot establish that tradeoff.

## 2. Where OpenEvolve and general-purpose LLMs fit

[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) is an open-source evolutionary coding framework inspired by AlphaEvolve. It provides infrastructure for proposing programs, evaluating candidates and managing a population of alternatives. We used OpenEvolve-based search with a project-specific biological evaluator and control interface; we did not invent the underlying search framework.

[AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) is related methodological context: LLM-generated code is tested by automated evaluators and improved through feedback. It is not the system that produced the reported P95/P98 search, and its published achievements are not evidence for this project's results.

The project-specific research is in making this idea concrete for protein modeling: expose decisions at meaningful points inside native sampling; supply current-structure observations without revealing the target answer; measure quality and work separately; preserve valid outputs; and test a frozen program beyond its development examples.

The development loop is agentic in the limited sense that software repeatedly proposes code, runs tools and uses feedback. **Deployment is not a conversational agent.** P95/P98 execute on CPUs with no LLM calls. No language-model weights were fine-tuned in this study; the object being improved was external control code.

## 3. Why this is a computational-biology question

For the loop-modeling task, several apparently sensible choices can conflict. Additional sampling may find a lower-energy conformation, but that need not be closer to the experimental structure. A database candidate can be inexpensive, but selecting it does not establish that it is suitable for every input. A physically valid starting structure can still be inaccurate.

We therefore kept distinct measures of local and global coordinate error, local and global modeled energy, geometric validity and computational work. The design of these measurements is part of the research, not bookkeeping around an otherwise complete AI solution. [Metric definitions and retained disagreements](closeout/RESULTS.md#metric-definitions).

The distinction between **validation** and **evaluation** matters. Code checks reject illegal programs or unsupported decisions. Geometry checks address declared structural conditions. Reference-based measurements assess proximity to an experimental structure on a benchmark. None is a general certificate of biological function. A program can pass the first checks and still make the last outcome worse; the external results preserve such examples.

The implication is not that a language model independently understands all the biology. It is that **domain knowledge, reliable native operations and measurable feedback can define a useful search space for a general-purpose model**. The evidence here concerns structural computation, not a newly discovered biochemical mechanism or experimentally improved enzyme.

## 4. The learned output is inspectable

Consider this exact excerpt from the frozen [P98 source](../src/p95p98/policies/p98.py), with its original comments:

```python
elif control['cleanup_only'] and control['cleanup_ready']:
    # Initialization acceptance has resolved. Stop alone.
    decision['stop'] = True
elif control['response_ready']:
    # Native acceptance was confirmed in the same epoch.
    # Stop alone; native_low remains the native endpoint.
    decision['stop'] = True
```

This is an excerpt, not a standalone implementation. Earlier code establishes the flags from measured geometry, energies and confirmation of the native acceptance event. In plain language: **after a qualifying lightweight response has been resolved, the program can stop further search rather than blindly finish the full schedule**. It leaves endpoint delivery to the native machinery.

Other branches track progress and conditionally modify an acceptance-temperature multiplier. The presence of a rule or an explanatory comment does not prove its benefit. Its value must be checked against the observed execution and outputs. Nor does readable code eliminate selection bias or overfitting: the development panel influenced which programs were retained.

For that reason, the repository connects four layers: **original proposal → frozen source → recorded native decisions → measured external result**. The public discovery examples include an invalid proposal, not just successful stories. The external counters are terminal totals; the accompanying detailed callbacks are sparse samples, not a complete replay. [Evidence index](closeout/EVIDENCE_INDEX.md).

## 5. What the experiments show

### Routing and control together

On BENCH48, P95/P98 used **16.11% / 25.13% of the matched native NGK total logical work**, with 48 geometry-valid outputs each versus 47 for NGK. This was the development set: 48 inputs from 32 homology components. Both programs had worse raw RMSD on the hard subgroup despite favorable aggregate tradeoffs. [All development results](closeout/RESULTS.md).

Each recorded 11 database calls, 37 NGK-refinement calls and two NGK-rebuild calls. Thus retrieval was part of the workflow, but the programs were not simply returning database structures on most inputs. These totals do not causally apportion savings among retrieval, stopping and other decisions. [Original action coverage](closeout/results/action_coverage.json).

### A benefit that does not require retrieval

The external test used six CASP15 targets, with one AlphaFold2 and one ESMFold starting structure per target. The already-frozen P95/P98 programs made **no database calls in any of their 24 runs**. On the AlphaFold2 condition, P98 used **14.45 seconds of mean method CPU versus 216.94 seconds for native warm-start NGK**, or **6.66% of its CPU**, with slightly lower mean local backbone RMSD: **1.602 versus 1.630 Å**.

The behavior was observable: every AlphaFold2 run recorded a voluntary stop, with **0, 0, 13, 2, 0 and 27 KIC attempts**. Against the fixed short-NGK control, P98 used 29.83% of the CPU and had lower mean local RMSD (1.602 versus 1.817 Å). This is useful evidence that the frozen program can control native sampling, not merely switch to a cheap database route. [Per-run counters](closeout/casp15/mc_control_counts.csv).

There are two essential boundaries. First, P98's mean local RMSD remained **0.0053 Å above the untouched AlphaFold2 sources**: this result concerns the cost and outcome of additional refinement, not a better AlphaFold predictor. Second, on the ESMFold condition P98 used **151.50% of native NGK CPU** and had mean local RMSD 5.743 Å versus 5.433 Å for the sources. Both starting conditions were specified before testing and remain reported. [Complete source-stratified tables](closeout/casp15/INTERPRETATION.md).

This evidence rules out retrieval as the explanation for the observed AlphaFold2-condition savings. It does not isolate the effect of acceptance temperature from stopping, retention and minimization, or prove that LLM search outperforms a matched manual or random search. There are six target units and one seed; no statistical equivalence or universal improvement is claimed.

## 6. Approximately 100 proposals, not an exhausted research direction

The run recorded **101 starts, 100 returned programs and 99 legal programs evaluated on the 48-input panel**. P95 and P98 are named for their proposal indices. Their selection late in the run is part of the provenance, not proof that performance would keep improving indefinitely. [Exact counts and selection history](closeout/DISCOVERY.md#counts-without-conflating-the-denominators).

This limited study nevertheless produced reusable control code and a measurable, non-retrieval benefit on new inputs. That is the proof of concept: a general-purpose model contributed executable scientific heuristics, and the resulting program could be tested separately from the model that proposed it.

Limited proposal count should not be confused with negligible total effort. The retained discovery account includes about **380 accounted route-CPU hours** for proposal evaluations, including reuse, and about **21.5 million tokens** in known model-use receipts. Interface development and scientific setup are separate. Those are not the per-input deployment costs, a reconciled currency bill or a promise of a one-weekend turnaround. [Cost definitions](closeout/RESULTS.md#cost-boundaries).

Larger datasets, longer searches and different control interfaces are reasonable research directions. Their benefit has not been measured here. Freezing this run is what makes the external comparison meaningful; these results are not made stronger by silently replacing P95/P98 after seeing them.

## 7. Beyond one modeling engine

There is a general distinction between **executing the same computation more efficiently** and **learning which computations are worth executing**. This study addresses the second. It is complementary to implementation optimization and to better structure predictors, rather than a replacement for either.

Rosetta is a concrete environment in which inputs, physical operations and decision points can be specified. The externally supplied AlphaFold2/ESMFold structures demonstrate one way a learned predictor and a classical sampling tool can meet through an inspectable controller. That does not guarantee their combination is always useful: the untreated-source and ESMFold comparisons show why it must be tested.

An analogous program-search question could be posed for docking search, simulation resource allocation or candidate screening **when the relevant actions and trustworthy evaluation can be defined**. These are prospective applications, not experiments performed in this repository. Changing the backend may require new observations, checks and a new program search; the present thresholds are not advertised as universal.

**The research direction is AI-assisted discovery of scientific algorithms. The demonstrated result is a bounded, inspectable example in protein-loop computation—with both a concrete success and a concrete limit.**

## Read or reproduce the reported summaries

[Discovery and original code edits](closeout/DISCOVERY.md) · [Development results](closeout/RESULTS.md) · [External results and behavior](closeout/casp15/INTERPRETATION.md) · [Installation](../README.md#installation)

From the package root, the three commands below use only the shipped code/record checks and scalar data; they neither retrain nor execute protein modeling:

```sh
python3 docs/closeout/discovery/verify.py
python3 docs/closeout/results/summarize.py
python3 docs/closeout/casp15/summarize.py
```

The [native runtime documentation](NATIVE_RUNTIME.md) preserves algorithm provenance and licensing. This independent application does not imply endorsement by OpenEvolve, AlphaEvolve or the underlying modeling-tool authors.
