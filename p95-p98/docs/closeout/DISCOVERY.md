# How P95 and P98 were discovered

P95 and P98 are **LLM-discovered control programs**. During development, an LLM proposed edits to a Python `decide(view)` function; the host applied those edits, enforced the interface and evaluated the resulting program on BENCH48. Deployment executes the frozen function and makes no LLM calls.

## Task, contributions and boundaries

The human-directed work defined the scientific question—how to trade loop-model quality against computation—and specified source-only observations, five evaluation objectives, budgets and controls. Native Monte Carlo integration and infrastructure repair used coding assistants; these engineering contributions are separate from the evolved policies. The search model proposed control-program changes from supplied parent/peer code and TRAIN feedback. The host performed patch application, static/interface checks, native execution, final-structure evaluation and archive updates. These records do not include a controlled comparison establishing that LLM search outperforms human-written rules or random search.

BENCH48 contained 48 development inputs (16 W, 16 S, 16 hard), grouped into 32 components. The five separate, component-balanced objectives were local RMSD, global RMSD, fixed local energy, fixed global energy and efficient delivery. No scalar overall winner was prespecified. The runtime ceiling was 1800 CPU seconds, 1800 logical-work units and 5400 active-wall seconds per input, shared across actions. The resumed search allowed at most 100 additional reservations after P1, with at most two candidates per wave and completed evaluation/archive assimilation before the next wave. These limits are transcribed in the retained [P95 prompt excerpt](discovery/P95/prompt_excerpt.json).

Only the complete `decide(view)` control function was mutable. Input sequences, movable regions, seeds, native physical operators, resources and evaluator remained host-owned. Runtime views contained source/current-state geometry and fixed energies, remaining work, available operations and bounded history; they excluded reference coordinates, target RMSD, PDB/file identifiers and held-out results. Development feedback could contain reference-quality TRAIN measurements. It was input to subsequent code proposals, never a deployment observation.

| Interface allowed | Frozen P95/P98 actually use |
|---|---|
| Select qualified outer actions and retained parent states | Database, NGK refinement/rebuilding, minimization and delivery branches; actual action counts are retained in the receipts |
| Bounded outer state archive and JSON memory | Retained outer parents and trajectory-local diagnostic memory |
| Native acceptance, explicit acceptance probability, or temperature multiplier | Native acceptance or a 0.75 multiplier; no direct probability override |
| Inner stop, archive/restore and delivery controls | Voluntary stops and native-low delivery; no custom inner save/restore |
| Native proposal controls within the interface | No non-native KIC perturbation implementation |

## Counts, without conflating the denominators

The [101-row proposal ledger](discovery/proposals.csv) joins retained reservation, iteration, model-use and evaluation records. [Compact receipts](discovery/receipts.json) preserve the selected original fields and precise floats. They are extracts, not newly issued historical receipts.

| Quantity | Count | Meaning |
|---|---:|---|
| Reservations | 101 | P1 plus 100 additional proposals |
| Model starts | 101 | Includes P96's recorded start and lost answer |
| Returned source programs | 100 | P96 has no recoverable source |
| Statically legal programs executed/evaluated | 99 | Each produced 48 VALID final rows and complete MolProbity receipts |
| Recorded proposal outcomes | 100 | Includes P45's 48 INVALID_POLICY/fallback records; its invalid code was not executed |
| Final archive entries | 54 | 34 distinct source programs plus 20 migration copies |
| Final database entries | 123 | 103 distinct sources (100 returned plus three controls), plus 20 migration copies |

`cost_record` identifies whether both token and evaluation receipts exist, not whether every cost category is known. P96's usage is missing. The 100 known response receipts total 21,531,286 tokens; no paid API calls were recorded. Route CPU and logical work include accounted reuse and are distinct from new physical server consumption, LLM waiting time and money spent. Cloud currency cost was not measured.

## Four retained evidence chains

Each successful extraction includes an exact parent from the final checkpoint, its identity, a real prompt excerpt, the complete model SEARCH/REPLACE answer, the resulting source, a generated unified diff, and original evaluation fields. [Case index](discovery/cases.json) gives full identities and the private original-record hashes. Code commentary is part of the model output, not evidence that its proposed mechanism worked.

1. **P45 — rejected candidate.** [Prompt](discovery/P45/prompt_excerpt.json) → [actual answer](discovery/P45/answer.txt) → [parent](discovery/P45/parent.py) / [diff](discovery/P45/change.diff) / [child](discovery/P45/child.py) → [historical evaluation](discovery/P45/historical_evaluation.json). The parent source starts `12cb693e32ac`; the returned source starts `962e8ad0772b`. The proposed changes include a bounded alternative polish parent and strain-dependent stopping. The retained result records 48 `INVALID_POLICY` stops, zero candidate actions and 48 UNINTERPRETABLE dispositions. MolProbity was completed on fallback evidence; this is not 48 successful executions of P45. P45 did not enter the final Pareto set.

2. **P95 — RMSD-oriented archive member.** [Prompt](discovery/P95/prompt_excerpt.json) → [answer](discovery/P95/answer.txt) → [parent](discovery/P95/parent.py) / [diff](discovery/P95/change.diff) / [child](discovery/P95/child.py) → [evaluation](discovery/P95/historical_evaluation.json). Exact parent archive ID: `df85832e-5ede-45a5-a920-6398be3551bd`; parent source starts `64e892c16a3a`. The answer changes repeat-descent eligibility and qualifies progress/stopping by measured local strain. The returned SHA-256 is `6c2330e612f4c2000d9965bd45d666c3ca26a74473b994b5ba4c513a06bb5ed8`, identical to the released policy. It achieved 48 VALID endpoints and entered the final Pareto archive. It attained the maximum local/global RMSD fitness of the search (P101 tied those quality values with lower efficiency). This describes a post-search selection on development data.

3. **P96 — consumed model call with no answer.** [Retained prompt excerpt](discovery/P96/prompt_excerpt.json) and [case record](discovery/cases.json) preserve the attempted proposal. Its original event log contains `turn/started`; the preserved `CONSUMED_NO_RESULT` record reports no recoverable answer, native calls or fitness and prohibits replacement. The parent is not recorded in the assimilated iteration, so no parent or code diff is invented. P96 consumed its reservation and remains in the ledger with unknown model usage.

4. **P98 — balanced post-search example.** [Prompt](discovery/P98/prompt_excerpt.json) → [answer](discovery/P98/answer.txt) → [parent](discovery/P98/parent.py) / [diff](discovery/P98/change.diff) / [child](discovery/P98/child.py) → [evaluation](discovery/P98/historical_evaluation.json). Exact parent archive ID: `ec56c34d-e25c-4aa9-94bf-df230438d271`; parent source starts `9b265b2f2a0e`. The answer proposes strain-qualified patience, one endpoint polish and confirmed low-strain exits. Returned SHA-256: `533a5549d5d8722f0ea43ce418c009a589c288696d906e4dd5e386945fd0fd83`, identical to the release. It produced 48 VALID endpoints, joined the final Pareto archive and exceeded P1 on all five frozen axes. It was a balanced retrospective example, not a prespecified scalar winner. Hard-case raw RMSD regressed against native NGK; the [results report](RESULTS.md) retains that distinction.

P97 had a request rejected for input size before model start; its existing reservation was recovered. The final report records later result-transfer interruptions reconciled from completed remote outputs without repeating model/native evaluations. Such transport events are distinct from a malformed policy, runtime policy error, exhausted CPU/wall budget, geometric invalidity and poor reference quality. The ledger retains stop and timeout summaries rather than turning these into a common “failed iteration” count.

## What checks establish

The restricted-source validator is `src/p95p98/policy_runtime/core.py::validate_source`; outer decisions are checked by `controller.py::validate_route`, and inner decisions by the policy contract. Static legality checks the program grammar, not structure quality. Native execution and CPU/wall outcomes are recorded separately. Source geometry checks establish the declared physical validity conditions. Reference RMSD and fixed energies evaluate different properties; MolProbity completion records completed diagnostics, not a catalytic-function test. The release's 54 focused software tests are not 54 structure experiments.

The offline command below checks all ledger joins/counts, evaluation denominators, retained source identities, exact parent-to-child SEARCH/REPLACE replay for P45/P95/P98 and released-policy identity. It does not execute the policy, rerun a validator, call an LLM or recompute structures. Its PASS result is present-day evidence consistency, not a historical validation receipt or reproduction of stochastic search.

```sh
python3 docs/closeout/discovery/verify.py
```

Run from the release directory. Prompt excerpts contain only exact initial system paragraphs and user objective/metric lines; APIs, peer code and extended feedback are omitted explicitly. Account identifiers, machine paths, private communication and transport envelopes are excluded. Full prompts and original records remain in the private workspace with an extraction provenance map. The public material contains control-program source and compact results, not the proprietary native runtime or databases.
