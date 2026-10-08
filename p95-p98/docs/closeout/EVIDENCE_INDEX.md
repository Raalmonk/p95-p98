# Evidence index

This page maps our claims to the records behind them. For the big question (can an LLM-guided search over programs find useful, readable rules for spending compute on biomolecular calculations?), start with the [research overview](../RESEARCH_OVERVIEW.md). P95 and P98 are the frozen programs produced by one limited experiment toward that question.

This publication brings together three separate bodies of evidence, listed below. Writing these docs involved no new structure calculations, LLM calls, policy changes, or choosing of samples.

| Evidence | What it supports | What it does not show |
|---|---|---|
| [Discovery records](DISCOVERY.md) | Traceable records of LLM-proposed changes to the frozen control programs, including real rejections and cases with no answer | That LLM search beats human or random search in a controlled test |
| [BENCH48 development results](RESULTS.md) | Large recorded trade-offs between quality and work for combined routing and native control, on the development set | Performance on an independent test, or that all savings came from database lookup |
| [CASP15 direct-source supplement](casp15/INTERPRETATION.md) | Useful early stopping of Monte Carlo (MC) search, without database lookup, on six AlphaFold2 predictions; external CPU and quality results that depend on the starting model | Gains everywhere, average improvement over AlphaFold2 itself, or a benefit from the temperature schedule on its own |
| [Earlier General pilot](GENERAL_PILOT.md) | A limited refinement comparison after the common NGK rebuild succeeded, with preparation problems kept on record | A fair test of database routing as a replacement for that required rebuild |

Notes on the CASP15 and General studies:

- The CASP15 comparison completed 48 method runs and 60 evaluations of starting and final structures. All geometry flags were valid. MolProbity was skipped.
- Its 12 starting models cover six targets. They are not 12 independent proteins.
- The user stopped the older General computation. Its evidence is kept separate.
- This publication does not reopen either study.

## Recompute without native runtimes

From the package root:

```sh
python3 docs/closeout/discovery/verify.py
python3 docs/closeout/results/summarize.py
python3 docs/closeout/casp15/summarize.py
```

What each one does:

1. **Discovery:** replays the original patches and checks that identities join up correctly.
2. **Development:** rebuilds the descriptive summaries from 144 scalar rows.
3. **CASP15:** checks all 48 scalar rows and 24 saved policy/counter extracts, then prints results split by starting model.

These are offline consistency checks. They are not new biological validation, and they do not exactly replay the random trajectories.

## Key data

- [Development scalars](results/per_input.csv)
- [Development invocation coverage](results/action_coverage.json)
- [CASP15 scalars](casp15/results_per_input.csv)
- [Native counters](casp15/mc_control_counts.csv)
- [Compact callback evidence](casp15/mc_control_evidence.json)

Full native logs and proprietary runtimes and databases are not included. The compact callback file holds sparse samples, while the native counters are end-of-run totals.
