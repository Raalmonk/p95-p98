# Figure caption

**Loop modeling: compute and quality.** Unnamed-P95/P98 are frozen evolved programs. All methods retain the same 48 planned inputs, except the online Agent pilots with three inputs each.

**A:** Passed/planned counts use the fixed full-atom checks, not the absence of all MolProbity anomalies. **B:** Per-input recorded modeling/control CPU includes failed attempts and measured-cost reuse, but excludes final scoring, MolProbity, shared resource construction and LLM wait. **C-D:** Derived CA RMSD uses one non-loop scaffold fit; local covers the modeled loop union, global all mapped CA atoms. **E-F:** Existing ref2015 energies retain their frozen local regions. Symmetric-log axes retain every extreme value and use original REU. Right-hand numeric summaries in B-F are medians in original units: seconds, Å and REU, respectively. No missing value is imputed.

Available sample sizes are listed below; RMSD and energy counts apply to both their local and global panels. The 48 development inputs comprise 32 W/S and 16 hard inputs, spanning 32 homology components.

| Method | n CPU | n RMSD | n energy |
| --- | ---: | ---: | ---: |
| Unnamed-P95 | 48 | 48 | 48 |
| Unnamed-P98 | 48 | 48 | 48 |
| NGK | 48 | 48 | 48 |
| ProMod3 | 48 | 48 | 45 |
| Sphinx | 48 | 18 | 16 |
| FREAD | 48 | 28 | 0 |
| Agent-Luna | 3 | 3 | 3 |
| Agent-Astra | 3 | 3 | 3 |

Blue identifies P95/P98; controls are gray. Circles denote W/S inputs, diamonds hard inputs, hollow markers outputs not meeting full-atom validity. Vertical strokes mark medians. Agent rows contain real points and medians only, separated from the full BENCH48 methods. All six Agent outputs were emergency deliveries after format or request/network/wall-limit failures. Their model waits were 74-231 s/input (Luna) and 767-895 s/input (Astra).

ProMod3 is the full native pipeline. Sphinx is an independent adapted reproduction using MSL sidechains. FREAD uses a rebuilt library and supplies backbone RMSD, but no comparable full-atom energies. Returned structures with available coordinates remain in the RMSD panels even when they fail full-atom validity. Missing structures and energies retain their planned denominators and are not replaced by zero.

The RMSD display uses one direct prediction-to-reference Kabsch alignment on all mapped non-loop Cα pairs. The same transform is applied to the actual modeled-loop union for local RMSD and to all mapped Cα pairs for global RMSD. These derived display measurements are separate from the frozen development objectives. Energy uses the fixed ref2015 score with backbone hydrogen-bond pair decomposition; local energy sums the original declared region, which includes additional context for W/S inputs, while global energy sums the complete structure. Values are Rosetta energy units (REU).

Full-atom validity checks sequence, required heavy atoms, source chemistry/connectivity and fixed geometry thresholds; completing MolProbity diagnostics is a separate status. Recorded CPU includes each method's retained failed attempts and exact measured preparation assigned to its pipeline. Whole-route reuse retains the original measured route cost. Shared database construction and model wait are separate costs. These development-set comparisons describe the selected programs and do not establish independent generalization.
