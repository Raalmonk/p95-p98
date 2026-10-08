# Fixed CASP15 retained-results report

48 positions: 12 inputs per method, 6 proteins, 2 source models, seed20261007. MolProbity skipped.
Values below summarize retained records only. Missing/error values are N/A, never zero. Metric means use the displayed available-value count; delta = endpoint minus paired source.

## Method CPU (seconds; outer method receipts only)

| Method | Positions | Complete labels | CPU n | Mean | Median | Total | Prior repair total | Cumulative total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P95 | 12 | 12 | 12 | 144.893177 | 174.381117 | 1738.718122 | 2.142635 | 1740.860757 |
| P98 | 12 | 12 | 12 | 130.894443 | 15.768155 | 1570.733322 | 2.123902 | 1572.857224 |
| native_NGK | 12 | 12 | 12 | 190.104051 | 214.899402 | 2281.248618 | 123.756355 | 2405.004973 |
| short_NGK | 12 | 12 | 12 | 41.574026 | 43.981930 | 498.888315 | 28.159726 | 527.048041 |

## Retained action counts

| Method | Positions with recorded action counts | Action totals |
|---|---:|---|
| P95 | 12 | {"minimize": 10, "ngk_refine": 12} |
| P98 | 12 | {"minimize": 10, "ngk_refine": 12} |
| native_NGK | 0 | {} |
| short_NGK | 0 | {} |

Action totals use terminal value.action_counts only; absent native-baseline counters are not inferred.
Resource build CPU, once and separate: 148.439991.
Preflight CPU, once and separate: 2.270524.
Source-evaluation CPU (12 unique inputs): 27.011579.
Endpoint-evaluation CPU: 117.630336.
Retained summary subtree CPU: 6392.683434; do not add this subtotal to the components above.

## Per-method metrics and source-model strata

| Source model | Method | Denominator | Geometry true/known | Metric | n | Mean | Median | Source mean | Paired delta n | Paired delta mean |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| All | P95 | 12 | 12/12 | local_bb_rmsd_A | 12 | 3.755054 | 2.660917 | 3.514533 | 12 | 0.240520 |
| All | P95 | 12 | 12/12 | global_ca_rmsd_A | 12 | 5.501944 | 2.002539 | 5.466560 | 12 | 0.035384 |
| All | P95 | 12 | 12/12 | local_energy_REU | 12 | -11.177006 | -9.705972 | 33.475934 | 12 | -44.652940 |
| All | P95 | 12 | 12/12 | global_energy_REU | 12 | 717.759072 | 70.871911 | 944.432386 | 12 | -226.673314 |
| All | P98 | 12 | 12/12 | local_bb_rmsd_A | 12 | 3.672060 | 2.504498 | 3.514533 | 12 | 0.157527 |
| All | P98 | 12 | 12/12 | global_ca_rmsd_A | 12 | 5.489605 | 2.003244 | 5.466560 | 12 | 0.023045 |
| All | P98 | 12 | 12/12 | local_energy_REU | 12 | -9.691819 | -8.729827 | 33.475934 | 12 | -43.167753 |
| All | P98 | 12 | 12/12 | global_energy_REU | 12 | 694.147210 | 75.117500 | 944.432386 | 12 | -250.285176 |
| All | native_NGK | 12 | 12/12 | local_bb_rmsd_A | 12 | 3.705032 | 2.613205 | 3.514533 | 12 | 0.190498 |
| All | native_NGK | 12 | 12/12 | global_ca_rmsd_A | 12 | 5.492155 | 2.016516 | 5.466560 | 12 | 0.025595 |
| All | native_NGK | 12 | 12/12 | local_energy_REU | 12 | -7.791554 | -4.921272 | 33.475934 | 12 | -41.267488 |
| All | native_NGK | 12 | 12/12 | global_energy_REU | 12 | 695.404649 | 46.482689 | 944.432386 | 12 | -249.027738 |
| All | short_NGK | 12 | 12/12 | local_bb_rmsd_A | 12 | 3.757258 | 2.674481 | 3.514533 | 12 | 0.242724 |
| All | short_NGK | 12 | 12/12 | global_ca_rmsd_A | 12 | 5.513406 | 1.997464 | 5.466560 | 12 | 0.046846 |
| All | short_NGK | 12 | 12/12 | local_energy_REU | 12 | -5.402263 | -4.489572 | 33.475934 | 12 | -38.878197 |
| All | short_NGK | 12 | 12/12 | global_energy_REU | 12 | 714.866604 | 53.981646 | 944.432386 | 12 | -229.565782 |
| AlphaFold2 | P95 | 6 | 6/6 | local_bb_rmsd_A | 6 | 1.754758 | 1.728073 | 1.596308 | 6 | 0.158450 |
| AlphaFold2 | P95 | 6 | 6/6 | global_ca_rmsd_A | 6 | 3.170027 | 1.496676 | 3.146206 | 6 | 0.023821 |
| AlphaFold2 | P95 | 6 | 6/6 | local_energy_REU | 6 | -13.137329 | -12.740516 | -4.360523 | 6 | -8.776806 |
| AlphaFold2 | P95 | 6 | 6/6 | global_energy_REU | 6 | -317.202776 | -311.554884 | -308.610319 | 6 | -8.592457 |
| AlphaFold2 | P98 | 6 | 6/6 | local_bb_rmsd_A | 6 | 1.601585 | 1.256404 | 1.596308 | 6 | 0.005277 |
| AlphaFold2 | P98 | 6 | 6/6 | global_ca_rmsd_A | 6 | 3.145773 | 1.468491 | 3.146206 | 6 | -0.000433 |
| AlphaFold2 | P98 | 6 | 6/6 | local_energy_REU | 6 | -10.060377 | -9.786555 | -4.360523 | 6 | -5.699854 |
| AlphaFold2 | P98 | 6 | 6/6 | global_energy_REU | 6 | -314.523645 | -307.803870 | -308.610319 | 6 | -5.913326 |
| AlphaFold2 | native_NGK | 6 | 6/6 | local_bb_rmsd_A | 6 | 1.629710 | 1.287578 | 1.596308 | 6 | 0.033402 |
| AlphaFold2 | native_NGK | 6 | 6/6 | global_ca_rmsd_A | 6 | 3.147040 | 1.463511 | 3.146206 | 6 | 0.000834 |
| AlphaFold2 | native_NGK | 6 | 6/6 | local_energy_REU | 6 | -10.142982 | -8.398046 | -4.360523 | 6 | -5.782459 |
| AlphaFold2 | native_NGK | 6 | 6/6 | global_energy_REU | 6 | -321.169870 | -311.266743 | -308.610319 | 6 | -12.559551 |
| AlphaFold2 | short_NGK | 6 | 6/6 | local_bb_rmsd_A | 6 | 1.817442 | 1.261192 | 1.596308 | 6 | 0.221134 |
| AlphaFold2 | short_NGK | 6 | 6/6 | global_ca_rmsd_A | 6 | 3.213949 | 1.672613 | 3.146206 | 6 | 0.067742 |
| AlphaFold2 | short_NGK | 6 | 6/6 | local_energy_REU | 6 | -10.383799 | -8.242105 | -4.360523 | 6 | -6.023276 |
| AlphaFold2 | short_NGK | 6 | 6/6 | global_energy_REU | 6 | -328.076454 | -319.683675 | -308.610319 | 6 | -19.466135 |
| ESMFold | P95 | 6 | 6/6 | local_bb_rmsd_A | 6 | 5.755349 | 5.484039 | 5.432758 | 6 | 0.322591 |
| ESMFold | P95 | 6 | 6/6 | global_ca_rmsd_A | 6 | 7.833861 | 5.932359 | 7.786914 | 6 | 0.046947 |
| ESMFold | P95 | 6 | 6/6 | local_energy_REU | 6 | -9.216683 | -5.071898 | 71.312390 | 6 | -80.529074 |
| ESMFold | P95 | 6 | 6/6 | global_energy_REU | 6 | 1752.720921 | 1163.639634 | 2197.475091 | 6 | -444.754171 |
| ESMFold | P98 | 6 | 6/6 | local_bb_rmsd_A | 6 | 5.742535 | 5.505086 | 5.432758 | 6 | 0.309777 |
| ESMFold | P98 | 6 | 6/6 | global_ca_rmsd_A | 6 | 7.833436 | 5.932419 | 7.786914 | 6 | 0.046522 |
| ESMFold | P98 | 6 | 6/6 | local_energy_REU | 6 | -9.323261 | -6.843792 | 71.312390 | 6 | -80.635652 |
| ESMFold | P98 | 6 | 6/6 | global_energy_REU | 6 | 1702.818066 | 1154.278021 | 2197.475091 | 6 | -494.657026 |
| ESMFold | native_NGK | 6 | 6/6 | local_bb_rmsd_A | 6 | 5.780354 | 5.557380 | 5.432758 | 6 | 0.347595 |
| ESMFold | native_NGK | 6 | 6/6 | global_ca_rmsd_A | 6 | 7.837269 | 5.940188 | 7.786914 | 6 | 0.050356 |
| ESMFold | native_NGK | 6 | 6/6 | local_energy_REU | 6 | -5.440126 | -1.799012 | 71.312390 | 6 | -76.752516 |
| ESMFold | native_NGK | 6 | 6/6 | global_energy_REU | 6 | 1711.979167 | 1156.599955 | 2197.475091 | 6 | -485.495924 |
| ESMFold | short_NGK | 6 | 6/6 | local_bb_rmsd_A | 6 | 5.697073 | 5.423013 | 5.432758 | 6 | 0.264315 |
| ESMFold | short_NGK | 6 | 6/6 | global_ca_rmsd_A | 6 | 7.812863 | 5.929819 | 7.786914 | 6 | 0.025949 |
| ESMFold | short_NGK | 6 | 6/6 | local_energy_REU | 6 | -0.420728 | -0.103131 | 71.312390 | 6 | -71.733118 |
| ESMFold | short_NGK | 6 | 6/6 | global_energy_REU | 6 | 1757.809662 | 1175.069438 | 2197.475091 | 6 | -439.665429 |

## Protein-level means (two source models per method)

| Protein | Method | Positions | Metric | n | Mean | Paired delta n | Paired delta mean |
|---|---|---:|---|---:|---:|---:|---:|
| T1104 | P95 | 2 | method_cpu_seconds | 2 | 55.200309 | 0 | N/A |
| T1104 | P95 | 2 | local_bb_rmsd_A | 2 | 1.547509 | 2 | 0.025256 |
| T1104 | P95 | 2 | global_ca_rmsd_A | 2 | 1.673440 | 2 | 0.000593 |
| T1104 | P95 | 2 | local_energy_REU | 2 | -15.954026 | 2 | -54.397876 |
| T1104 | P95 | 2 | global_energy_REU | 2 | 605.159752 | 2 | -155.534105 |
| T1104 | P98 | 2 | method_cpu_seconds | 2 | 11.359703 | 0 | N/A |
| T1104 | P98 | 2 | local_bb_rmsd_A | 2 | 1.541443 | 2 | 0.019191 |
| T1104 | P98 | 2 | global_ca_rmsd_A | 2 | 1.674085 | 2 | 0.001238 |
| T1104 | P98 | 2 | local_energy_REU | 2 | -13.767886 | 2 | -52.211736 |
| T1104 | P98 | 2 | global_energy_REU | 2 | 605.825116 | 2 | -154.868741 |
| T1104 | native_NGK | 2 | method_cpu_seconds | 2 | 86.393903 | 0 | N/A |
| T1104 | native_NGK | 2 | local_bb_rmsd_A | 2 | 1.647569 | 2 | 0.125317 |
| T1104 | native_NGK | 2 | global_ca_rmsd_A | 2 | 1.681819 | 2 | 0.008972 |
| T1104 | native_NGK | 2 | local_energy_REU | 2 | -6.562358 | 2 | -45.006208 |
| T1104 | native_NGK | 2 | global_energy_REU | 2 | 607.107892 | 2 | -153.585965 |
| T1104 | short_NGK | 2 | method_cpu_seconds | 2 | 20.923207 | 0 | N/A |
| T1104 | short_NGK | 2 | local_bb_rmsd_A | 2 | 1.731860 | 2 | 0.209607 |
| T1104 | short_NGK | 2 | global_ca_rmsd_A | 2 | 1.696661 | 2 | 0.023814 |
| T1104 | short_NGK | 2 | local_energy_REU | 2 | 5.870105 | 2 | -32.573745 |
| T1104 | short_NGK | 2 | global_energy_REU | 2 | 614.395668 | 2 | -146.298189 |
| T1109 | P95 | 2 | method_cpu_seconds | 2 | 12.922740 | 0 | N/A |
| T1109 | P95 | 2 | local_bb_rmsd_A | 2 | 0.478425 | 2 | 0.029150 |
| T1109 | P95 | 2 | global_ca_rmsd_A | 2 | 9.824199 | 2 | 0.000132 |
| T1109 | P95 | 2 | local_energy_REU | 2 | -28.809171 | 2 | -4.709239 |
| T1109 | P95 | 2 | global_energy_REU | 2 | -132.391071 | 2 | -13.390475 |
| T1109 | P98 | 2 | method_cpu_seconds | 2 | 12.785630 | 0 | N/A |
| T1109 | P98 | 2 | local_bb_rmsd_A | 2 | 0.478425 | 2 | 0.029150 |
| T1109 | P98 | 2 | global_ca_rmsd_A | 2 | 9.824199 | 2 | 0.000132 |
| T1109 | P98 | 2 | local_energy_REU | 2 | -28.809171 | 2 | -4.709239 |
| T1109 | P98 | 2 | global_energy_REU | 2 | -132.391071 | 2 | -13.390475 |
| T1109 | native_NGK | 2 | method_cpu_seconds | 2 | 259.891542 | 0 | N/A |
| T1109 | native_NGK | 2 | local_bb_rmsd_A | 2 | 0.462894 | 2 | 0.013619 |
| T1109 | native_NGK | 2 | global_ca_rmsd_A | 2 | 9.824191 | 2 | 0.000124 |
| T1109 | native_NGK | 2 | local_energy_REU | 2 | -25.880702 | 2 | -1.780770 |
| T1109 | native_NGK | 2 | global_energy_REU | 2 | -156.501225 | 2 | -37.500629 |
| T1109 | short_NGK | 2 | method_cpu_seconds | 2 | 57.309214 | 0 | N/A |
| T1109 | short_NGK | 2 | local_bb_rmsd_A | 2 | 0.472564 | 2 | 0.023288 |
| T1109 | short_NGK | 2 | global_ca_rmsd_A | 2 | 9.824318 | 2 | 0.000251 |
| T1109 | short_NGK | 2 | local_energy_REU | 2 | -26.019169 | 2 | -1.919237 |
| T1109 | short_NGK | 2 | global_energy_REU | 2 | -147.430123 | 2 | -28.429526 |
| T1123 | P95 | 2 | method_cpu_seconds | 2 | 266.764440 | 0 | N/A |
| T1123 | P95 | 2 | local_bb_rmsd_A | 2 | 7.726517 | 2 | 0.439126 |
| T1123 | P95 | 2 | global_ca_rmsd_A | 2 | 11.269306 | 2 | -0.007920 |
| T1123 | P95 | 2 | local_energy_REU | 2 | -5.455240 | 2 | -67.099999 |
| T1123 | P95 | 2 | global_energy_REU | 2 | 2502.040126 | 2 | -251.795508 |
| T1123 | P98 | 2 | method_cpu_seconds | 2 | 167.649831 | 0 | N/A |
| T1123 | P98 | 2 | local_bb_rmsd_A | 2 | 7.701625 | 2 | 0.414234 |
| T1123 | P98 | 2 | global_ca_rmsd_A | 2 | 11.268114 | 2 | -0.009112 |
| T1123 | P98 | 2 | local_energy_REU | 2 | -2.897363 | 2 | -64.542121 |
| T1123 | P98 | 2 | global_energy_REU | 2 | 2505.797141 | 2 | -248.038492 |
| T1123 | native_NGK | 2 | method_cpu_seconds | 2 | 205.357848 | 0 | N/A |
| T1123 | native_NGK | 2 | local_bb_rmsd_A | 2 | 7.722653 | 2 | 0.435261 |
| T1123 | native_NGK | 2 | global_ca_rmsd_A | 2 | 11.268101 | 2 | -0.009125 |
| T1123 | native_NGK | 2 | local_energy_REU | 2 | -3.052174 | 2 | -64.696932 |
| T1123 | native_NGK | 2 | global_energy_REU | 2 | 2498.515657 | 2 | -255.319976 |
| T1123 | short_NGK | 2 | method_cpu_seconds | 2 | 46.199268 | 0 | N/A |
| T1123 | short_NGK | 2 | local_bb_rmsd_A | 2 | 7.507139 | 2 | 0.219747 |
| T1123 | short_NGK | 2 | global_ca_rmsd_A | 2 | 11.269818 | 2 | -0.007408 |
| T1123 | short_NGK | 2 | local_energy_REU | 2 | -3.003697 | 2 | -64.648455 |
| T1123 | short_NGK | 2 | global_energy_REU | 2 | 2505.691018 | 2 | -248.144615 |
| T1139 | P95 | 2 | method_cpu_seconds | 2 | 247.176030 | 0 | N/A |
| T1139 | P95 | 2 | local_bb_rmsd_A | 2 | 5.368224 | 2 | 0.563790 |
| T1139 | P95 | 2 | global_ca_rmsd_A | 2 | 7.515177 | 2 | 0.060295 |
| T1139 | P95 | 2 | local_energy_REU | 2 | -5.370824 | 2 | -97.101339 |
| T1139 | P95 | 2 | global_energy_REU | 2 | 791.266574 | 2 | -318.574191 |
| T1139 | P98 | 2 | method_cpu_seconds | 2 | 249.098892 | 0 | N/A |
| T1139 | P98 | 2 | local_bb_rmsd_A | 2 | 4.887735 | 2 | 0.083301 |
| T1139 | P98 | 2 | global_ca_rmsd_A | 2 | 7.453744 | 2 | -0.001138 |
| T1139 | P98 | 2 | local_energy_REU | 2 | -0.935113 | 2 | -92.665627 |
| T1139 | P98 | 2 | global_energy_REU | 2 | 773.680935 | 2 | -336.159830 |
| T1139 | native_NGK | 2 | method_cpu_seconds | 2 | 220.895368 | 0 | N/A |
| T1139 | native_NGK | 2 | local_bb_rmsd_A | 2 | 4.876042 | 2 | 0.071608 |
| T1139 | native_NGK | 2 | global_ca_rmsd_A | 2 | 7.451608 | 2 | -0.003274 |
| T1139 | native_NGK | 2 | local_energy_REU | 2 | -2.432817 | 2 | -94.163332 |
| T1139 | native_NGK | 2 | global_energy_REU | 2 | 769.294564 | 2 | -340.546201 |
| T1139 | short_NGK | 2 | method_cpu_seconds | 2 | 49.772863 | 0 | N/A |
| T1139 | short_NGK | 2 | local_bb_rmsd_A | 2 | 4.823920 | 2 | 0.019487 |
| T1139 | short_NGK | 2 | global_ca_rmsd_A | 2 | 7.448314 | 2 | -0.006567 |
| T1139 | short_NGK | 2 | local_energy_REU | 2 | -4.140198 | 2 | -95.870713 |
| T1139 | short_NGK | 2 | global_energy_REU | 2 | 783.736476 | 2 | -326.104289 |
| T1187 | P95 | 2 | method_cpu_seconds | 2 | 133.496289 | 0 | N/A |
| T1187 | P95 | 2 | local_bb_rmsd_A | 2 | 3.828345 | 2 | 0.415938 |
| T1187 | P95 | 2 | global_ca_rmsd_A | 2 | 1.797589 | 2 | 0.143018 |
| T1187 | P95 | 2 | local_energy_REU | 2 | -7.546362 | 2 | -36.612120 |
| T1187 | P95 | 2 | global_energy_REU | 2 | 274.412747 | 2 | -92.027048 |
| T1187 | P98 | 2 | method_cpu_seconds | 2 | 220.224823 | 0 | N/A |
| T1187 | P98 | 2 | local_bb_rmsd_A | 2 | 3.847634 | 2 | 0.435226 |
| T1187 | P98 | 2 | global_ca_rmsd_A | 2 | 1.797649 | 2 | 0.143078 |
| T1187 | P98 | 2 | local_energy_REU | 2 | -11.502098 | 2 | -40.567856 |
| T1187 | P98 | 2 | global_energy_REU | 2 | 142.154980 | 2 | -224.284815 |
| T1187 | native_NGK | 2 | method_cpu_seconds | 2 | 234.196140 | 0 | N/A |
| T1187 | native_NGK | 2 | local_bb_rmsd_A | 2 | 3.904438 | 2 | 0.492031 |
| T1187 | native_NGK | 2 | global_ca_rmsd_A | 2 | 1.798208 | 2 | 0.143637 |
| T1187 | native_NGK | 2 | local_energy_REU | 2 | -7.216447 | 2 | -36.282205 |
| T1187 | native_NGK | 2 | global_energy_REU | 2 | 185.873336 | 2 | -180.566459 |
| T1187 | short_NGK | 2 | method_cpu_seconds | 2 | 46.988124 | 0 | N/A |
| T1187 | short_NGK | 2 | local_bb_rmsd_A | 2 | 4.381577 | 2 | 0.969170 |
| T1187 | short_NGK | 2 | global_ca_rmsd_A | 2 | 1.920617 | 2 | 0.266046 |
| T1187 | short_NGK | 2 | local_energy_REU | 2 | -2.090138 | 2 | -31.155896 |
| T1187 | short_NGK | 2 | global_energy_REU | 2 | 268.263993 | 2 | -98.175802 |
| T1194 | P95 | 2 | method_cpu_seconds | 2 | 153.799252 | 0 | N/A |
| T1194 | P95 | 2 | local_bb_rmsd_A | 2 | 3.581301 | 2 | -0.030138 |
| T1194 | P95 | 2 | global_ca_rmsd_A | 2 | 0.931952 | 2 | 0.016185 |
| T1194 | P95 | 2 | local_energy_REU | 2 | -3.926414 | 2 | -7.997067 |
| T1194 | P95 | 2 | global_energy_REU | 2 | 266.066305 | 2 | -528.718557 |
| T1194 | P98 | 2 | method_cpu_seconds | 2 | 124.247781 | 0 | N/A |
| T1194 | P98 | 2 | local_bb_rmsd_A | 2 | 3.575500 | 2 | -0.035939 |
| T1194 | P98 | 2 | global_ca_rmsd_A | 2 | 0.919837 | 2 | 0.004070 |
| T1194 | P98 | 2 | local_energy_REU | 2 | -0.239284 | 2 | -4.309938 |
| T1194 | P98 | 2 | global_energy_REU | 2 | 269.816161 | 2 | -524.968700 |
| T1194 | native_NGK | 2 | method_cpu_seconds | 2 | 133.889509 | 0 | N/A |
| T1194 | native_NGK | 2 | local_bb_rmsd_A | 2 | 3.616594 | 2 | 0.005155 |
| T1194 | native_NGK | 2 | global_ca_rmsd_A | 2 | 0.929003 | 2 | 0.013235 |
| T1194 | native_NGK | 2 | local_energy_REU | 2 | -1.604826 | 2 | -5.675480 |
| T1194 | native_NGK | 2 | global_energy_REU | 2 | 268.137667 | 2 | -526.647195 |
| T1194 | short_NGK | 2 | method_cpu_seconds | 2 | 28.251481 | 0 | N/A |
| T1194 | short_NGK | 2 | local_bb_rmsd_A | 2 | 3.626486 | 2 | 0.015047 |
| T1194 | short_NGK | 2 | global_ca_rmsd_A | 2 | 0.920707 | 2 | 0.004940 |
| T1194 | short_NGK | 2 | local_energy_REU | 2 | -3.030483 | 2 | -7.101137 |
| T1194 | short_NGK | 2 | global_energy_REU | 2 | 264.542593 | 2 | -530.242269 |

## Non-complete or unavailable evaluations

None.
