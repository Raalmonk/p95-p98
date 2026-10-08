# BENCH48 descriptive tables

The quality columns (RMSD and energy) in the first table are raw averages of the frozen (pre-specified) metrics over all 48 returned inputs; the cost columns are totals. The averages include the geometrically invalid result that NGK (next-generation kinematic closure, the native Rosetta loop-modeling baseline) returned at row 36. RMSD (root-mean-square deviation from the reference structure; lower is closer) is in Å, and energy is in REU (Rosetta energy units). These raw averages are not the component-balanced scoring objectives (the transformed, higher-is-better scores balanced across homology components). The pooled legacy RMSD averages mix two definitions: backbone atoms over an expanded region for the W and S input groups (W/S), and CA (alpha-carbon) atoms over the loop for hard inputs. So use the paired subgroup changes below to judge frozen-metric quality.

In the column headers, "MP complete" counts inputs where the MolProbity structure diagnostics finished. "Logical work" is the project's calibrated work unit, not seconds. "Accounted route CPU" is measured modeling CPU (processor) time, including failed attempts and reused preparation.

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

The next table shows average changes on inputs where both the method and NGK returned valid results: method minus NGK, so negative is better. NGK's one invalid hard input is excluded here but stays in the 48-input table above.

| Method | Group | Both-valid n / planned | Δ local RMSD | Δ global RMSD | Δ local energy | Δ global energy |
|---|---|---:|---:|---:|---:|---:|
| P95 | WS | 32/32 | -0.177382 | -0.069089 | 0.138180 | 18.439437 |
| P95 | hard | 15/16 | 0.873826 | 0.216342 | -28.333812 | 15.435016 |
| P98 | WS | 32/32 | -0.035327 | -0.014386 | -2.863966 | 7.617551 |
| P98 | hard | 15/16 | 0.352907 | 0.107234 | -30.896725 | 7.146576 |

The last table gives medians of the CA RMSD shown in the figure (computed after one shared alignment on the non-loop scaffold) and of the fixed energies. It covers all outputs, including NGK's invalid one, with n=48 per cell. These CA values are derived for the figure; they are not the frozen scoring objectives.

| Method | Local CA RMSD median (Å) | Global CA RMSD median (Å) | Local energy median (REU) | Global energy median (REU) |
|---|---:|---:|---:|---:|
| P95 | 0.819551 | 0.225938 | -24.173352 | -144.303246 |
| P98 | 0.779953 | 0.225200 | -30.680857 | -156.550432 |
| NGK | 0.877707 | 0.266807 | -24.358542 | -147.385832 |
