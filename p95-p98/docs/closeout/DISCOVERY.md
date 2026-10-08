# How P95 and P98 were discovered

P95 and P98 are control programs that came out of an LLM-guided search. During development, an LLM proposed edits to one Python function, `decide(view)`. Our host software applied each edit, checked that it followed the allowed interface, and scored the result on BENCH48, our 48-case development set. Once frozen, the programs run on their own. Deployment makes no LLM calls.

## What kind of study this is

We used an LLM to search over runnable programs that steer a scientific computation. [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) supplied the search machinery. We supplied the protein-modeling side: the decisions the program can make, the hooks into the modeling software (Rosetta and ProMod3), what the program can observe, and how it is scored. This is an independent application. We did not invent OpenEvolve or the underlying physical algorithms.

The search was small on purpose: about 100 proposals (exact counts below). "P95" and "P98" are just proposal numbers, not versions of some larger model. We froze both programs before the external test, so we could check whether their behavior carried over beyond the development inputs. We have not measured what a longer search, or a different application, would give.

The [research overview](../RESEARCH_OVERVIEW.md) explains the two levels of search (the protein shapes, and the programs that control that search) and shows a real stopping rule. This page documents what actually happened, using the original records rather than an after-the-fact story.

## Who did what, and the rules of the search

**People set the question and the rules.** The question was how to trade loop-model quality against compute. We chose what the program could observe (only information available from the starting structure), five scoring objectives, compute budgets, and comparison methods. Coding assistants helped wire up Rosetta's Monte Carlo sampler and fix infrastructure. That engineering is separate from the evolved programs.

**The LLM proposed code changes.** It saw a parent program, some peer programs, and feedback from the training cases.

**The host did everything else.** It applied patches, ran static and interface checks, ran the real modeling, scored the final structures, and updated the archive of candidates.

![How the programs were found, then deployed](../figures/search_loop.svg)

These records include no controlled test of LLM search against hand-written rules or random search, so we make no claim that the LLM beats them.

**The development set.** BENCH48 has 48 inputs: 16 W, 16 S and 16 hard. They fall into 32 groups of related proteins (homology components). We scored programs on five separate objectives, each balanced across those groups: local RMSD, global RMSD, fixed local energy, fixed global energy, and efficient delivery. (RMSD, root-mean-square deviation, measures how far a model's atoms are from the true structure.) We did not set up a single combined score or a single winner in advance.

**Budgets.** Each input could use at most 1800 CPU seconds, 1800 logical-work units and 5400 active wall-clock seconds, shared across all actions. After the first program (P1), the resumed search could reserve at most 100 more proposals, run at most two at a time, and had to finish scoring and archiving one wave before starting the next. These limits appear in the saved [P95 prompt excerpt](discovery/P95/prompt_excerpt.json).

**What the program could and couldn't touch.** Only the `decide(view)` function could change. The host owned the input sequences, the movable regions, random seeds, the physical operations, resources, and the scorer. At run time the program saw the starting and current geometry, fixed energies, remaining budget, available actions, and a limited history. It never saw the reference (true) coordinates, its RMSD to the target, PDB or file IDs, or held-out results. Training feedback to the LLM could include quality measured against reference structures, but that only shaped the next code proposal. It was never an input to a running program.

| What the interface allowed | What frozen P95/P98 actually use |
|---|---|
| Select qualified outer actions and retained parent states | Database, NGK refinement/rebuilding, minimization and delivery branches; actual action counts are retained in the receipts |
| Bounded outer state archive and JSON memory | Retained outer parents and trajectory-local diagnostic memory |
| Native acceptance, explicit acceptance probability, or temperature multiplier | Native acceptance or a 0.75 multiplier; no direct probability override |
| Inner stop, archive/restore and delivery controls | Voluntary stops and native-low delivery; no custom inner save/restore |
| Native proposal controls within the interface | No non-native KIC perturbation implementation |

(NGK is Rosetta's next-generation kinematic closure loop modeling. KIC is kinematic closure, the move NGK uses to reshape a loop.)

## The counts

Different counts here have different denominators, so we list them separately. The [101-row proposal ledger](discovery/proposals.csv) joins the saved reservation, iteration, model-usage and scoring records. [Compact receipts](discovery/receipts.json) keep selected original fields with exact numbers. They are extracts from the original records, not newly issued receipts.

| Quantity | Count | Meaning |
|---|---:|---|
| Reservations | 101 | P1 plus 100 additional proposals |
| Model starts | 101 | Includes P96's recorded start and lost answer |
| Returned source programs | 100 | P96 has no recoverable source |
| Statically legal programs executed/evaluated | 99 | Each produced 48 VALID final rows and complete MolProbity receipts |
| Recorded proposal outcomes | 100 | Includes P45's 48 INVALID_POLICY/fallback records; its invalid code was not executed |
| Final archive entries | 54 | 34 distinct source programs plus 20 migration copies |
| Final database entries | 123 | 103 distinct sources (100 returned plus three controls), plus 20 migration copies |

**Cost.** The `cost_record` field says whether both a token receipt and a scoring receipt exist. It does not mean every kind of cost is known. P96's usage is missing. The other 100 responses used 21,531,286 tokens in total, and no paid API calls were recorded. Route CPU and logical work include reused, already-measured work, so they are not the same as new server time, time spent waiting on the LLM, or money. We did not measure cloud cost in currency.

## Four example proposals, start to finish

Where we could recover the full record, we kept the exact parent program from the final checkpoint and its identity, a real excerpt of the prompt, the LLM's full SEARCH/REPLACE answer, the resulting program, a diff, and the original scoring fields. The [case index](discovery/cases.json) has full identities and hashes of the private original records. Comments inside the code were written by the LLM; they are not evidence that the idea worked.

1. **P45: rejected.** [Prompt](discovery/P45/prompt_excerpt.json) → [actual answer](discovery/P45/answer.txt) → [parent](discovery/P45/parent.py) / [diff](discovery/P45/change.diff) / [child](discovery/P45/child.py) → [historical evaluation](discovery/P45/historical_evaluation.json). Parent source hash starts `12cb693e32ac`; returned source starts `962e8ad0772b`. The LLM proposed a limited alternative parent for polishing and a stopping rule that depends on strain. The program was invalid: the record shows 48 `INVALID_POLICY` stops, zero candidate actions and 48 UNINTERPRETABLE outcomes. MolProbity ran on the fallback structures, so this is not 48 successful runs of P45. It did not make the final set of best trade-offs (the Pareto set).

2. **P95: RMSD-focused.** [Prompt](discovery/P95/prompt_excerpt.json) → [answer](discovery/P95/answer.txt) → [parent](discovery/P95/parent.py) / [diff](discovery/P95/change.diff) / [child](discovery/P95/child.py) → [evaluation](discovery/P95/historical_evaluation.json). Parent archive ID: `df85832e-5ede-45a5-a920-6398be3551bd`; parent source starts `64e892c16a3a`. The change adjusts when the program may repeat a descent, and ties progress and stopping to measured local strain. Returned SHA-256: `6c2330e612f4c2000d9965bd45d666c3ca26a74473b994b5ba4c513a06bb5ed8`, identical to the released program. It produced 48 VALID results, joined the final Pareto archive, and reached the search's top local and global RMSD scores (P101 tied on those but was less efficient). We picked it after the search, using development data.

3. **P96: model call used, no answer.** The [saved prompt excerpt](discovery/P96/prompt_excerpt.json) and [case record](discovery/cases.json) keep the attempt. The original log shows `turn/started`. The saved `CONSUMED_NO_RESULT` record shows no recoverable answer, no modeling calls and no score, and forbids replacing it. The parent was not recorded in the archived iteration, so we show no parent or diff rather than making one up. P96 used up its reservation and stays in the ledger with unknown model usage.

4. **P98: balanced.** [Prompt](discovery/P98/prompt_excerpt.json) → [answer](discovery/P98/answer.txt) → [parent](discovery/P98/parent.py) / [diff](discovery/P98/change.diff) / [child](discovery/P98/child.py) → [evaluation](discovery/P98/historical_evaluation.json). Parent archive ID: `ec56c34d-e25c-4aa9-94bf-df230438d271`; parent source starts `9b265b2f2a0e`. The change adds strain-aware patience, a single final polish, and early exits once low strain is confirmed. Returned SHA-256: `533a5549d5d8722f0ea43ce418c009a589c288696d906e4dd5e386945fd0fd83`, identical to the release. It produced 48 VALID results, joined the final Pareto archive, and beat P1 on all five objectives. We chose it after the fact as a balanced example, not as a pre-declared winner. On hard cases its raw RMSD was worse than standard NGK; the [results report](RESULTS.md) keeps that visible.

**Other events.** P97's request was rejected for being too large before the model started, and its reservation was recovered. Some later result transfers were interrupted; we reconciled them from the finished remote outputs without rerunning the model or the modeling. Transfer problems are different from a malformed program, a runtime error, running out of CPU or wall time, invalid geometry, or poor quality. The ledger keeps stop and timeout summaries separately instead of lumping them into one "failed iteration" count.

## What the checks do and don't show

- `src/p95p98/policy_runtime/core.py::validate_source` checks program source. `controller.py::validate_route` checks outer decisions. The policy contract checks inner decisions.
- Passing the static check means the program follows the allowed grammar. It says nothing about structure quality.
- Real execution, CPU time and wall time are recorded separately.
- Source geometry checks confirm the stated physical validity rules.
- Reference RMSD and fixed energies measure different things.
- A completed MolProbity run means the diagnostics finished. It is not a test of biological function.
- The release's 54 software tests are code tests, not 54 structure experiments.

The offline command below checks all ledger joins and counts, the scoring denominators, the saved source identities, an exact replay of the parent-to-child SEARCH/REPLACE edits for P45, P95 and P98, and that the released programs match. It does not run the programs, rerun a validator, call an LLM or recompute structures. A PASS means today's evidence files are consistent with each other. It is not a historical validation, and it does not re-run the search itself, which was stochastic (random choices affected each run).

```sh
python3 docs/closeout/discovery/verify.py
```

Run it from the release directory.

**What is public.** Prompt excerpts contain only the exact opening system paragraphs and the user's objective and metric lines. API details, peer code and longer feedback are explicitly left out. So are account IDs, machine paths, private messages and transport wrappers. Full prompts and original records stay in our private workspace, with a map of how each extract was made. The public release has the control-program source and compact results, not the proprietary Rosetta runtime or databases.
