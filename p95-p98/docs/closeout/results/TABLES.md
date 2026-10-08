# BENCH48 descriptive tables

All quality values in the first table are frozen raw means over all 48 returned inputs, including NGK row36 geometry-invalid output. RMSD is in Å; energy is in REU. These are not component-balanced fitness. Pooled legacy RMSD mixes W/S backbone expanded-region and hard CA loop-region definitions: use the paired subgroup changes for frozen-quality interpretation.

| Method | Returned/planned | Valid | MP complete | Local RMSD | Global RMSD | Local energy | Global energy | Logical work sum | Accounted route CPU (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P95 | 48/48 | 48 | 48 | 1.784395 | 0.601618 | -19.357086 | -190.719561 | 8518.318 | 9974.949 |
| P98 | 48/48 | 48 | 48 | 1.716311 | 0.603991 | -22.159428 | -200.524289 | 13285.407 | 14903.911 |
| NGK | 48/48 | 47 | 48 | 1.627905 | 0.579563 | 189.270822 | 39.975720 | 52864.757 | 55905.890 |

| Method / cost | Sum ratio | Median input ratio | Ratio of medians | Paired n |
|---|---:|---:|---:|---:|
| P95 / logical_work_not_seconds | 16.113416% | 2.143247% | 1.971724% | 48 |
| P95 / cpu_seconds | 17.842394% | 4.003270% | 3.705760% | 48 |
| P98 / logical_work_not_seconds | 25.130934% | 2.297841% | 1.837406% | 48 |
| P98 / cpu_seconds | 26.658927% | 4.501912% | 3.457686% | 48 |

Paired valid raw mean changes below are method minus NGK; negative is better. The invalid NGK hard input remains in the main 48-input table above.

| Method | Group | Both-valid n / planned | Δ local RMSD | Δ global RMSD | Δ local energy | Δ global energy |
|---|---|---:|---:|---:|---:|---:|
| P95 | WS | 32/32 | -0.177382 | -0.069089 | 0.138180 | 18.439437 |
| P95 | hard | 15/16 | 0.873826 | 0.216342 | -28.333812 | 15.435016 |
| P98 | WS | 32/32 | -0.035327 | -0.014386 | -2.863966 | 7.617551 |
| P98 | hard | 15/16 | 0.352907 | 0.107234 | -30.896725 | 7.146576 |

Existing common scaffold-fit CA display metrics and fixed-energy medians; all available outputs including the NGK invalid output, n=48 per cell. These CA values are derived figure metrics, not the frozen fitness.

| Method | Local CA RMSD median (Å) | Global CA RMSD median (Å) | Local energy median (REU) | Global energy median (REU) |
|---|---:|---:|---:|---:|
| P95 | 0.819551 | 0.225938 | -24.173352 | -144.303246 |
| P98 | 0.779953 | 0.225200 | -30.680857 | -156.550432 |
| NGK | 0.877707 | 0.266807 | -24.358542 | -147.385832 |
