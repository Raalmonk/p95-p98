# Figure caption

**Loop modeling: compute and quality.** "Unnamed-P95" and "Unnamed-P98" are the frozen LLM-evolved programs. Every method runs the same 48 planned inputs, except the two online Agent pilots, which ran three inputs each.

**Panels**

- **A:** Passed/planned counts. "Passed" means the fixed full-atom checks, not that MolProbity found no problems at all.
- **B:** CPU per input for modeling and control. Includes failed attempts and reused, already-measured work. Excludes final scoring, MolProbity, building shared resources, and LLM wait time.
- **C-D:** CA RMSD (root-mean-square deviation of CA atoms from the reference structure) after one alignment on the non-loop scaffold. Local covers the modeled loops; global covers all matched CA atoms.
- **E-F:** The existing ref2015 energies. Local energy keeps its original frozen local region; global energy covers the whole structure. The axes use a symmetric log scale so every extreme value is shown, in original REU.

The numbers on the right of panels B-F are medians in original units: seconds, Å and REU. We never fill in missing values.

**Sample sizes.** RMSD and energy counts apply to both the local and global panels. The 48 development inputs are 32 W/S and 16 hard inputs, from 32 homology components (groups of related proteins).

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

**How to read the markers.** P95 and P98 are blue; comparison methods are gray. Circles are W/S inputs and diamonds are hard inputs. Hollow markers are outputs that failed full-atom validity. Vertical strokes mark medians.

**Agent rows** show real points and medians only, and sit apart from the full BENCH48 methods. All six Agent outputs were emergency deliveries after format, request or network failures, or after hitting the wall-clock time limit. Model wait was 74-231 s per input for Luna and 767-895 s per input for Astra.

**Comparison methods.** NGK is Rosetta's standard next-generation kinematic closure loop modeling. ProMod3 is the full native ProMod3 pipeline. Sphinx is an independent, adapted reproduction that uses MSL for side chains. FREAD uses a rebuilt fragment library; it gives backbone RMSD but no comparable full-atom energies.

**Missing and invalid outputs.** Returned structures with coordinates stay in the RMSD panels even if they fail full-atom validity. Missing structures and energies still count in the planned totals and are never replaced by zero.

**Metric details.** The RMSD display uses one direct Kabsch alignment of the model onto the reference over all matched non-loop Cα pairs. The same alignment is then used for local RMSD (the modeled-loop union) and global RMSD (all matched Cα pairs). These display values are separate from the frozen development objectives. Energy uses Rosetta's fixed ref2015 score with backbone hydrogen-bond pair decomposition, in Rosetta energy units (REU). Local energy sums the original declared region, which includes extra surrounding residues for W/S inputs. Global energy sums the whole structure.

Full-atom validity checks the sequence, required heavy atoms, chemistry and connectivity from the starting structure, and fixed geometry thresholds. Finishing the MolProbity diagnostics is a separate status. Recorded CPU includes each method's failed attempts and the exact measured preparation assigned to its pipeline. When a whole route was reused, it keeps its original measured cost. Shared database building and model wait are counted separately.

**Caveat:** these are development-set comparisons of programs we selected on this same data. They do not show that the results generalize to new proteins.
