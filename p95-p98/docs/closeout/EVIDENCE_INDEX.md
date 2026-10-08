# Evidence index

This publication joins three distinct bodies of evidence. No new structural calculation, LLM call, policy change or sample selection was performed for this documentation update.

| Evidence | What it supports | What it does not establish |
|---|---|---|
| [Discovery records](DISCOVERY.md) | Traceable LLM-proposed changes to frozen control programs, including real rejection and missing-answer cases | A controlled advantage of LLM search over human or random search |
| [BENCH48 development results](RESULTS.md) | Large recorded quality/work tradeoffs for combined routing and native control on the development panel | Independent test performance or attribution of all savings to retrieval |
| [CASP15 direct-source supplement](casp15/INTERPRETATION.md) | Useful non-retrieval MC stopping on six AlphaFold2 predictions; source-dependent external CPU/quality behavior | Universal gains, average improvement over AlphaFold2 itself, or an isolated temperature-schedule benefit |
| [Earlier General pilot](GENERAL_PILOT.md) | Limited refinement comparison after successful common NGK reconstruction, with preparation problems retained | A fair test of using database routing instead of that compulsory reconstruction |

The CASP15 comparison completed 48 method positions and 60 source/endpoint evaluations. All geometry flags were valid; MolProbity was skipped. Its 12 starting models represent six targets, not 12 independent proteins. The older General computation was stopped by the user; its evidence is separate. Neither study is reopened by this publication.

## Recompute without native runtimes

From the package root:

```sh
python3 docs/closeout/discovery/verify.py
python3 docs/closeout/results/summarize.py
python3 docs/closeout/casp15/summarize.py
```

The discovery command checks original patch replay and identity joins. The development command regenerates descriptive summaries from 144 scalar rows. The CASP15 command checks all 48 scalar rows and 24 retained policy/counter extracts, then prints source-stratified results. These are offline consistency checks, not new biological validation or exact replay of stochastic trajectories.

Key data: [development scalars](results/per_input.csv), [development invocation coverage](results/action_coverage.json), [CASP15 scalars](casp15/results_per_input.csv), [native counters](casp15/mc_control_counts.csv), [compact callback evidence](casp15/mc_control_evidence.json). Full native logs and proprietary runtimes/databases are not bundled. The compact callbacks are sparse samples, while reported native counters are terminal totals.
