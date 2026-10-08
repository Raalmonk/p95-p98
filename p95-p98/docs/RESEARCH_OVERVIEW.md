# From AI-written code to testable scientific algorithms

## The idea in one minute

Most visible uses of AI in molecular research produce a prediction: a sequence, a structure, a binding score. We explored a different kind of output: **a program that decides how a scientific computation should proceed**.

Here's how it works. A researcher decides what the program may change and how to score it. A language model proposes code changes. We check those programs, run them and compare them, and the results guide the next proposals. The end product is ordinary code. You can read it and run it without calling the language model again.

**NGNGK is one concrete test of this idea, in protein modeling.** Its two released programs, P95 and P98, control existing operations. They don't replace the protein physics. In a small test on new proteins, P98 saved a lot of compute for one kind of starting model, without using database lookups. For another kind of starting model, the advantage disappeared. Together, those results show both what this approach can do and where it stops working.

[Main results](../README.md#external-monte-carlo-control) · [Discovery evidence](closeout/DISCOVERY.md) · [Complete external interpretation](closeout/casp15/INTERPRETATION.md)

## 1. Two searches at different levels

This study has two separate searches.

**The structure search looks for protein shapes.** The sequence and the surrounding structure are fixed. The modeling software changes one chosen loop, adjusts the sidechains and scores each result. It uses NGK (next-generation kinematic closure), Rosetta's established loop-modeling method. Inside NGK, KIC (kinematic closure) reshapes the loop while keeping its ends attached. Monte Carlo acceptance lets the search sometimes take a worse move, so it can explore instead of always grabbing the lowest-energy option. [Native method and provenance](METHOD.md).

**The program search looks for better ways to control those calculations.** An LLM edits a Python decision function. That function picks an available operation, looks at current measurements and the search history, keeps a candidate, and decides whether to continue or stop. The host code, not the editable function, owns the input, the physics operations, the resource definitions and the scoring rules. [Actual editable boundary](closeout/DISCOVERY.md#who-did-what-and-the-rules-of-the-search).

![Program discovery, routing and the controlled NGK refinement loop](figures/Training_Workflow_NGK.svg)

The program search is not just a faster version of the structure search. It can change **which calculations happen at all**, so its result can differ from a long, fixed protocol. That means we have to measure both cost and structure quality. A cheaper run is only useful if the quality tradeoff is acceptable, and passing software tests can't tell you that.

## 2. Where OpenEvolve and general-purpose LLMs fit

[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) is an open-source framework for evolving code, inspired by AlphaEvolve. It handles proposing programs, scoring them and managing a population of alternatives. We built on it, adding our own biology scoring and control interface. We did not invent the search framework.

[AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) is related background: LLM-written code is tested by automatic evaluators and improved through feedback. It is not the system that ran our search, and its published results are not evidence for ours.

Our own contribution is making this idea work for protein modeling. That meant:

- exposing decisions at useful points inside the native sampling;
- giving the program observations of the current structure without revealing the right answer;
- measuring quality and work separately;
- keeping valid outputs; and
- testing a frozen program on cases it wasn't developed on.

The development loop is "agentic" only in a narrow sense: software repeatedly proposes code, runs tools and uses the feedback. **Running P95/P98 involves no conversational agent.** They run on CPUs with no LLM calls. We fine-tuned no language-model weights. What improved was external control code.

## 3. Why this is a computational-biology question

In loop modeling, several reasonable-sounding choices can pull against each other:

- More sampling may find a lower-energy shape, but that shape isn't necessarily closer to the experimental structure.
- A database candidate is cheap, but picking it doesn't mean it suits every input.
- A starting structure can be physically valid and still be wrong.

So we tracked several measures separately: local and global coordinate error, local and global modeled energy, geometric validity and computational work. Designing these measurements is part of the research, not paperwork around a finished AI result. [Metric definitions and retained disagreements](closeout/RESULTS.md#metric-definitions).

**Passing checks is not the same as getting a good result.** Code checks reject illegal programs and unsupported decisions. Geometry checks confirm stated structural conditions. Reference-based measurements tell you how close a model is to an experimental structure on a benchmark. None of these certifies biological function. A program can pass the first two kinds of checks and still make the last one worse, and our external results include such cases.

The lesson is not that a language model understands the biology on its own. It's that **domain knowledge, reliable native operations and measurable feedback can define a useful search space for a general-purpose model**. Our evidence is about structural computation. We did not discover a biochemical mechanism or experimentally improve an enzyme.

## 4. You can read what was learned

Here is an exact excerpt from the frozen [P98 source](../src/p95p98/policies/p98.py), with its original comments:

```python
elif control['cleanup_only'] and control['cleanup_ready']:
    # Initialization acceptance has resolved. Stop alone.
    decision['stop'] = True
elif control['response_ready']:
    # Native acceptance was confirmed in the same epoch.
    # Stop alone; native_low remains the native endpoint.
    decision['stop'] = True
```

This snippet doesn't run on its own. Earlier code sets these flags from measured geometry, energies and confirmation that native acceptance happened. In plain terms: **once a qualifying light-touch response has been resolved, the program can stop searching instead of blindly running the full schedule.** It leaves delivering the final structure to the native machinery.

Other branches track progress and, under some conditions, change an acceptance-temperature multiplier. A rule or a comment in the code doesn't prove the rule helps. You have to check it against what actually ran and what came out. Readable code also doesn't remove selection bias or overfitting: the development set influenced which programs we kept.

That's why the repo links four layers: **original proposal → frozen source → recorded native decisions → measured external result**. The public discovery examples include an invalid proposal, not only successes. The external counters are final totals. The detailed callback logs that come with them are sparse samples, not a full replay. [Evidence index](closeout/EVIDENCE_INDEX.md).

## 5. What the experiments show

### Routing and control together

**On BENCH48, P95 and P98 used 16.11% and 25.13% of NGK's total logical work** ("logical work" is the project's calibrated work unit, not CPU seconds). Each produced 48 geometrically valid outputs, versus 47 for NGK. BENCH48 is our development set: 48 inputs from 32 groups of related proteins. Overall the tradeoffs looked good, but both programs had worse raw RMSD (distance from the experimental structure) on the hard subgroup. [All development results](closeout/RESULTS.md).

Each program made 11 database calls, 37 NGK-refinement calls and 2 NGK-rebuild calls. So the database was part of the workflow, but the programs were not just returning database structures for most inputs. These totals don't tell us how much of the savings came from retrieval, from stopping or from other decisions. [Original action coverage](closeout/results/action_coverage.json).

### A benefit that does not require retrieval

**On new proteins starting from AlphaFold2 models, P98 used 6.66% of the CPU time of native warm-start NGK, with slightly lower mean local RMSD (1.602 vs. 1.630 Å) and no database calls.**

The external test used six CASP15 targets (from a blind structure-prediction competition). Each target had one AlphaFold2 and one ESMFold starting structure. The already-frozen P95/P98 made no database calls in any of their 24 runs. With AlphaFold2 starts, P98 averaged 14.45 s of method CPU versus 216.94 s for native warm-start NGK, or 6.66%. Its mean local backbone RMSD was slightly lower: 1.602 vs. 1.630 Å.

The stops were recorded: every AlphaFold2 run stopped by choice, after 0, 0, 13, 2, 0 and 27 KIC attempts. Against a fixed short NGK run, P98 used 29.83% of the CPU and had lower mean local RMSD (1.602 vs. 1.817 Å). This is useful evidence that the frozen program can control native sampling, not just switch to a cheap database route. [Per-run counters](closeout/casp15/mc_control_counts.csv).

![P98 stopped early on AlphaFold2 starts](figures/casp15_early_stopping.svg)

Two limits matter here:

- It doesn't beat AlphaFold2. P98's mean local RMSD stayed 0.0053 Å worse than the untouched AlphaFold2 models. The result is about the cost and outcome of extra refinement, not a better predictor.
- The advantage did not hold with ESMFold starts. There, P98 used 151.50% of NGK's CPU, and its mean local RMSD was 5.743 Å versus 5.433 Å for the starting models.

We chose both starting conditions before testing, and we report both. [Complete source-stratified tables](closeout/casp15/INTERPRETATION.md).

This rules out database lookup as the reason for the AlphaFold2 savings. It does not separate the effect of the temperature change from stopping, candidate retention and minimization. It also doesn't show that LLM search beats a matched manual or random search. The test had six targets and one seed. We don't claim statistical equivalence or improvement in general.

## 6. About 100 proposals, not an exhausted direction

The run recorded **101 starts, 100 returned programs and 99 legal programs scored on the 48-input set**. P95 and P98 are named after their proposal numbers. That they came late in the run is part of the record. It doesn't prove performance would keep improving. [Exact counts and selection history](closeout/DISCOVERY.md#the-counts).

Even this small study produced reusable control code and a measurable benefit on new inputs that didn't depend on the database. That's the proof of concept: a general-purpose model contributed runnable scientific rules of thumb, and we could test the resulting program separately from the model that wrote it.

A small number of proposals doesn't mean little effort. The discovery records include about **380 accounted route-CPU hours** for scoring proposals (including reuse) and about **21.5 million tokens** in known model-usage receipts. Building the interface and setting up the science were extra. These figures are not per-input running costs, a reconciled bill, or a promise you can do this in a weekend. [Cost definitions](closeout/RESULTS.md#cost-boundaries).

Bigger datasets, longer searches and different control interfaces are reasonable next steps, but we haven't measured whether they help. Freezing this run is what makes the external comparison fair. Quietly swapping in better programs after seeing the results would not make these findings stronger.

## 7. Beyond one modeling engine

There's a difference between running the same computation faster and learning which computations are worth running. This study is about the second. It complements code optimization and better structure predictors. It doesn't replace either.

Rosetta gave us a concrete setting where inputs, physics operations and decision points could be pinned down. Feeding in AlphaFold2 and ESMFold structures shows one way a learned predictor and a classical sampling tool can work together through a readable controller. That pairing isn't always useful: the comparisons with untreated starting models and with ESMFold show why it has to be tested.

A similar program search could apply to docking, allocating simulation resources or screening candidates, as long as the relevant actions and a trustworthy evaluation can be defined. These are possible future uses. We haven't run them here. A new backend may need new observations, new checks and a new program search. The current thresholds are not meant to be universal.

**The broad direction is AI-assisted discovery of scientific algorithms. What we've shown is one bounded, readable example in protein-loop modeling, with one clear success and one clear limit.**

## Read or reproduce the reported summaries

[Discovery and original code edits](closeout/DISCOVERY.md) · [Development results](closeout/RESULTS.md) · [External results and behavior](closeout/casp15/INTERPRETATION.md) · [Installation](../README.md#installation)

From the package root, run the three commands below. They only check the shipped code and records and summarize the saved numbers. They don't retrain anything or run protein modeling.

```sh
python3 docs/closeout/discovery/verify.py
python3 docs/closeout/results/summarize.py
python3 docs/closeout/casp15/summarize.py
```

The [native runtime documentation](NATIVE_RUNTIME.md) covers where the algorithms come from and their licenses. This is an independent project. It doesn't imply endorsement by OpenEvolve, AlphaEvolve or the authors of the underlying modeling tools.
